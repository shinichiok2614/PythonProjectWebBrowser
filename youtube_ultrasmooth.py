# youtube_ultrasmooth.py
import os
import sys
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget, QWidget, QVBoxLayout
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

# ----- CONFIG -----
HOME = "https://www.youtube.com"
# Patterns we will block (video codecs / heavy js / trackers)
BLOCK_PATTERNS = [
    # video codecs - try to block requests that hint at VP9/AV1 or webm
    r"vp9", r"vp09", r"av01", r"webm", r"mime=video/webm",
    # trackers / analytics / ads (reduce extra JS/request load)
    r"doubleclick\.net", r"googlesyndication\.com", r"pagead", r"google-analytics\.com",
    r"analytics.js", r"gtag/js", r"adsystem\.com", r"ads\.php",
    # prefetch / prerender resources
    r"prefetch", r"preload", r"prerender"
]
# compile regex
BLOCK_RE = [re.compile(pat, re.IGNORECASE) for pat in BLOCK_PATTERNS]

# Some domains we always allow (core YouTube resources)
WHITELIST_DOMAINS = ["youtube.com", "googlevideo.com", "ytimg.com", "gstatic.com"]

# Set chromium flags to attempt to reduce usage of experimental codecs / GPU issues
# Note: flags change with Chromium versions; these are best-effort.
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS",
                     "--disable-gpu --disable-features=UseChromeOSDirectVideoDecoder,WebRTCUseHwH264Decoding "
                     "--autoplay-policy=user-gesture-required --enable-low-end-device-mode")

# ----- Interceptor -----
class YouTubeInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        host = info.requestUrl().host()

        # Always allow core youtube hosts
        for d in WHITELIST_DOMAINS:
            if d in host:
                break
        else:
            # Not in whitelist -> if matches obvious tracker or ad pattern, block
            for r in BLOCK_RE:
                if r.search(url):
                    info.block(True)
                    #print("BLOCKED (3rd-party):", url)
                    return

        # Heuristic: try to block requests that explicitly request webm/vp9/av1 segments or manifests
        # Many youtube dash manifests or segment URLs contain "mime=video/webm" or "codecs=vp9" etc.
        # If found, and host is googlevideo.com we still try to block VP9/AV1 video but allow audio.
        try:
            if ("mime=video" in url.lower() or "codecs=" in url.lower()) and any(x in url.lower() for x in ("vp9", "vp09", "av01", "webm")):
                # allow audio-only requests
                if "mime=audio" in url.lower() or "itag=" in url.lower() and re.search(r"\b(itag=)*(140|141|251|250|249)\b", url):
                    return
                # block video segments that match VP9/AV1/webm
                info.block(True)
                #print("BLOCKED codec video:", url)
                return
        except Exception:
            pass

        # Avoid blocking other essential resources
        return

# ----- Browser UI -----
class UltraSmoothBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube MiniBrowser — Ultra Smooth")
        self.resize(1200, 800)

        # Profile tuned
        self.profile = QWebEngineProfile("yt_ultrasmooth_profile", self)
        # keep memory cache smaller and force memory cache to reduce disk IO
        self.profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self.profile.setHttpCacheMaximumSize(80 * 1024 * 1024)  # 80MB
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        # user agent: prefer older Chrome that commonly negotiates H.264; this can influence manifest selection
        # (no guarantee)
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36")
        self.profile.setHttpUserAgent(ua)
        # attach interceptor
        self.profile.setRequestInterceptor(YouTubeInterceptor())

        # Global webengine settings to reduce heavy rendering
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, False)
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, False)
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)

        # central tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # toolbar
        nav = QToolBar("nav")
        self.addToolBar(nav)

        back = QAction("◀", self); back.triggered.connect(lambda: self.current().back()); nav.addAction(back)
        forward = QAction("▶", self); forward.triggered.connect(lambda: self.current().forward()); nav.addAction(forward)
        reload = QAction("⟳", self); reload.triggered.connect(lambda: self.current().reload()); nav.addAction(reload)
        home = QAction("🏠", self); home.triggered.connect(self.go_home); nav.addAction(home)
        nav.addSeparator()

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.load_url_from_bar)
        nav.addWidget(self.urlbar)

        zoom_in = QAction("A+", self); zoom_in.triggered.connect(self.zoom_in); nav.addAction(zoom_in)
        zoom_out = QAction("A-", self); zoom_out.triggered.connect(self.zoom_out); nav.addAction(zoom_out)
        zoom_reset = QAction("A0", self); zoom_reset.triggered.connect(self.zoom_reset); nav.addAction(zoom_reset)

        # init first tab
        self.add_tab(HOME)

    def add_tab(self, url):
        container = QWidget()
        layout = QVBoxLayout(container)
        view = QWebEngineView()
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)

        # Set per-page settings conservative
        s = view.settings()
        s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)   # YouTube needs JS
        s.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        s.setAttribute(QWebEngineSettings.LocalStorageEnabled, False)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)

        view.load(QUrl(url))
        view.urlChanged.connect(lambda u: self.urlbar.setText(u.toString()))
        layout.addWidget(view)
        container.setLayout(layout)
        idx = self.tabs.addTab(container, "YouTube")
        self.tabs.setCurrentIndex(idx)

        # apply small default zoom
        view.setZoomFactor(1.0)

    def current(self):
        widget = self.tabs.currentWidget()
        if not widget:
            return None
        view = widget.findChild(QWebEngineView)
        return view

    def load_url_from_bar(self):
        url = self.urlbar.text().strip()
        if not url:
            return
        if not url.startswith("http"):
            url = "https://" + url
        cur = self.current()
        if cur:
            cur.load(QUrl(url))

    def go_home(self):
        cur = self.current()
        if cur:
            cur.load(QUrl(HOME))

    def zoom_in(self):
        cur = self.current()
        if cur:
            cur.setZoomFactor(cur.zoomFactor() + 0.1)

    def zoom_out(self):
        cur = self.current()
        if cur:
            cur.setZoomFactor(max(0.2, cur.zoomFactor() - 0.1))

    def zoom_reset(self):
        cur = self.current()
        if cur:
            cur.setZoomFactor(1.0)

# ----- run -----
def main():
    # Use software GL if GPU causes instability (optional)
    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    app = QApplication(sys.argv)
    win = UltraSmoothBrowser()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
