import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

YOUTUBE_URL = "https://www.youtube.com/"

# --------------------------
#  SIMPLE YOUTUBE AD BLOCKER
# --------------------------
class YouTubeAdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        # Danh sách host / path chặn quảng cáo YouTube
        self.block_patterns = [
            "googlevideo.com",
            "doubleclick.net",
            "googlesyndication.com",
            "adservice.google.com",
            "pagead2.googlesyndication.com",
            "youtube.com/api/stats/ads",
        ]

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        for pat in self.block_patterns:
            if pat in url:
                info.block(True)
                # print(f"Blocked ad: {url}")
                return

# --------------------------
#  BROWSER TAB
# --------------------------
class BrowserTab(QWidget):
    def __init__(self, url, profile=None):
        super().__init__()
        layout = QVBoxLayout(self)
        self.web = QWebEngineView()
        if profile:
            page = QWebEnginePage(profile, self.web)
            self.web.setPage(page)
        self.web.setUrl(QUrl(url))
        layout.addWidget(self.web)
        self.setLayout(layout)

# --------------------------
#  MINI BROWSER
# --------------------------
class MiniBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube MiniBrowser")
        self.resize(1200, 800)
        self.zoom_factor = 1.0

        # --- PROFILE with ad blocker ---
        self.profile = QWebEngineProfile("YouTubeProfile", self)
        self.profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self.profile.setRequestInterceptor(YouTubeAdBlocker())

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(False)
        self.setCentralWidget(self.tabs)

        # --- Toolbar ---
        nav = QToolBar("Navigation")
        self.addToolBar(nav)

        back_btn = QAction("◀", self)
        back_btn.triggered.connect(lambda: self.current().back())
        nav.addAction(back_btn)

        forward_btn = QAction("▶", self)
        forward_btn.triggered.connect(lambda: self.current().forward())
        nav.addAction(forward_btn)

        reload_btn = QAction("⟳", self)
        reload_btn.triggered.connect(lambda: self.current().reload())
        nav.addAction(reload_btn)

        home_btn = QAction("🏠", self)
        home_btn.triggered.connect(self.go_home)
        nav.addAction(home_btn)
        nav.addSeparator()

        # Zoom
        zoom_in_btn = QAction("A+", self)
        zoom_in_btn.triggered.connect(self.zoom_in)
        nav.addAction(zoom_in_btn)

        zoom_out_btn = QAction("A-", self)
        zoom_out_btn.triggered.connect(self.zoom_out)
        nav.addAction(zoom_out_btn)

        zoom_reset_btn = QAction("A0", self)
        zoom_reset_btn.triggered.connect(self.zoom_reset)
        nav.addAction(zoom_reset_btn)

        # URL bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        nav.addWidget(self.urlbar)

        # --- First Tab ---
        self.add_tab(YOUTUBE_URL)

    # --------------------------
    #  TAB MANAGEMENT
    # --------------------------
    def add_tab(self, url):
        tab = BrowserTab(url, profile=self.profile)
        tab.web.urlChanged.connect(lambda u: self.urlbar.setText(u.toString()))
        self.tabs.addTab(tab, "YouTube")
        self.tabs.setCurrentWidget(tab)
        self.apply_zoom_to_tab(tab.web)

    def current(self):
        tab = self.tabs.currentWidget()
        return tab.web if tab else None

    # --------------------------
    #  NAVIGATION
    # --------------------------
    def navigate(self):
        url = self.urlbar.text().strip()
        if not url.startswith("http"):
            url = "https://" + url
        self.current().setUrl(QUrl(url))

    def go_home(self):
        self.current().setUrl(QUrl(YOUTUBE_URL))

    # --------------------------
    #  ZOOM
    # --------------------------
    def zoom_in(self):
        self.zoom_factor += 0.1
        self.apply_zoom_to_tab(self.current())

    def zoom_out(self):
        self.zoom_factor = max(0.2, self.zoom_factor - 0.1)
        self.apply_zoom_to_tab(self.current())

    def zoom_reset(self):
        self.zoom_factor = 1.0
        self.apply_zoom_to_tab(self.current())

    def apply_zoom_to_tab(self, web):
        if web:
            web.setZoomFactor(self.zoom_factor)

# --------------------------
#  RUN APP
# --------------------------
def main():
    app = QApplication(sys.argv)
    browser = MiniBrowser()
    browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
