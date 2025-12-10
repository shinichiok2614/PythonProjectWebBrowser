import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QToolBar, QAction
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage


YOUTUBE_AUDIO_CSS = """
video, ytd-player, #player video {
    display: none !important;
    visibility: hidden !important;
}
"""

HOME_PAGE = "https://www.youtube.com"

class AudioYouTubeBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Audio Browser")
        self.resize(1100, 700)

        # --- Profile tối ưu ---
        self.profile = QWebEngineProfile("YTAudioProfile", self)
        self.profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)

        # --- Web view ---
        self.web = QWebEngineView()
        page = QWebEnginePage(self.profile, self.web)  # tạo page với profile
        self.web.setPage(page)
        self.web.load(QUrl(HOME_PAGE))
        self.setCentralWidget(self.web)
        self.web.loadFinished.connect(self.inject_css)

        # --- Toolbar ---
        nav = QToolBar("Navigation")
        self.addToolBar(nav)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        nav.addWidget(self.urlbar)

        back_btn = QAction("◀", self)
        back_btn.triggered.connect(lambda: self.web.back())
        nav.addAction(back_btn)

        forward_btn = QAction("▶", self)
        forward_btn.triggered.connect(lambda: self.web.forward())
        nav.addAction(forward_btn)

        reload_btn = QAction("⟳", self)
        reload_btn.triggered.connect(lambda: self.web.reload())
        nav.addAction(reload_btn)

    def navigate(self):
        url = self.urlbar.text().strip()
        if not url.startswith("http"):
            url = "https://" + url
        self.web.load(QUrl(url))

    def inject_css(self):
        js = f"""
        (function() {{
            let style = document.createElement('style');
            style.innerHTML = `{YOUTUBE_AUDIO_CSS}`;
            document.head.appendChild(style);
        }})();
        """
        self.web.page().runJavaScript(js)
        self.urlbar.setText(self.web.url().toString())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AudioYouTubeBrowser()
    win.show()
    sys.exit(app.exec_())
