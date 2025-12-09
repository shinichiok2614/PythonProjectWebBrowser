import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

import re

HOME_PAGE = "https://www.google.com"


# --------------------------
#  AD BLOCK INTERCEPTOR
# --------------------------
class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()

        # Tập regex để nhận diện quảng cáo
        self.block_patterns = [
            r"doubleclick\.net",
            r"googlesyndication\.com",
            r"adsystem\.com",
            r"adservice\.google\.com",
            r"pagead\/",
            r"facebook\.com\/tr",
            r"\/banner\/",
            r"\/ads\/",
            r"\/advert",
            r"adserver",
            r"adtrack",
            r"tracking",
        ]
        self.block_regex = [re.compile(pat, re.IGNORECASE) for pat in self.block_patterns]

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        for regex in self.block_regex:
            if regex.search(url):
                info.block(True)
                return


# --------------------------
#  BROWSER TAB
# --------------------------
class BrowserTab(QWidget):
    def __init__(self, url=HOME_PAGE):
        super().__init__()
        layout = QVBoxLayout(self)

        self.web = QWebEngineView()
        self.web.setUrl(QUrl(url))

        layout.addWidget(self.web)
        self.setLayout(layout)


# --------------------------
#  MAIN BROWSER
# --------------------------
class MiniBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_hotkeys()
        self.dark_mode = False
        self.setWindowTitle("Mini Browser (AdBlock)")
        self.resize(1100, 700)

        # --- AdBlock ---
        self.setup_adblock()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_urlbar)

        self.setCentralWidget(self.tabs)

        # Toolbar
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

        zoom_in_btn = QAction("A+", self)
        zoom_in_btn.triggered.connect(self.zoom_in)
        nav.addAction(zoom_in_btn)

        zoom_out_btn = QAction("A-", self)
        zoom_out_btn.triggered.connect(self.zoom_out)
        nav.addAction(zoom_out_btn)

        zoom_reset_btn = QAction("A0", self)
        zoom_reset_btn.triggered.connect(self.zoom_reset)
        nav.addAction(zoom_reset_btn)

        nav.addSeparator()

        dark_btn = QAction("🌙", self)
        dark_btn.setStatusTip("Toggle Dark Mode")
        dark_btn.triggered.connect(self.toggle_dark_mode)
        nav.addAction(dark_btn)

        # Address bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        nav.addWidget(self.urlbar)

        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_tab(HOME_PAGE))
        nav.addAction(new_tab_btn)

        # First Tab
        self.add_tab(HOME_PAGE)

    def setup_adblock(self):
        profile = QWebEngineProfile.defaultProfile()
        interceptor = AdBlockInterceptor()
        profile.setRequestInterceptor(interceptor)
        print("AdBlock enabled!")

    def add_tab(self, url):
        tab = BrowserTab(url)
        tab.web.loadFinished.connect(lambda ok, w=tab.web: self.apply_dark_if_enabled(w))
        index = self.tabs.addTab(tab, "Tab")
        tab.web.titleChanged.connect(lambda t, i=index: self.tabs.setTabText(i, t[:30]))
        tab.web.urlChanged.connect(lambda u, i=index: self.url_changed(u, i))
        self.tabs.setCurrentIndex(index)

    def close_tab(self, i):
        if self.tabs.count() == 1:
            sys.exit()
        self.tabs.removeTab(i)

    def current(self):
        return self.tabs.currentWidget().web

    def navigate(self):
        text = self.urlbar.text().strip()
        if not text:
            return

        if not text.startswith("http"):
            if "." in text:
                text = "http://" + text
            else:
                from urllib.parse import quote_plus
                text = "https://www.google.com/search?q=" + quote_plus(text)

        self.current().setUrl(QUrl(text))

    def url_changed(self, url, index):
        if index == self.tabs.currentIndex():
            self.urlbar.setText(url.toString())

    def update_urlbar(self):
        w = self.current()
        if w:
            self.urlbar.setText(w.url().toString())

    def go_home(self):
        self.current().setUrl(QUrl(HOME_PAGE))

    def zoom_in(self):
        w = self.current()
        if w:
            current_zoom = w.zoomFactor()
            w.setZoomFactor(current_zoom + 0.1)

    def zoom_out(self):
        w = self.current()
        if w:
            current_zoom = w.zoomFactor()
            w.setZoomFactor(max(0.2, current_zoom - 0.1))

    def zoom_reset(self):
        w = self.current()
        if w:
            w.setZoomFactor(1.0)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode

        if self.dark_mode:
            js = """
            (function() {
                let css = `
                    html, body {
                        background: #111 !important;
                        filter: invert(1) hue-rotate(180deg) !important;
                    }
                    img, video, canvas {
                        filter: invert(1) hue-rotate(180deg) !important;
                    }
                `;
                let style = document.createElement('style');
                style.id = "dark_mode_css";
                style.innerText = css;
                document.head.appendChild(style);
            })();
            """
            icon = "☀"
        else:
            js = """
            (function() {
                let style = document.getElementById("dark_mode_css");
                if (style) style.remove();
            })();
            """
            icon = "🌙"

        # đổi icon nút
        self.sender().setText(icon)

        # inject vào trang hiện tại
        self.current().page().runJavaScript(js)

    def apply_dark_if_enabled(self, web):
        if not self.dark_mode:
            return

        js = """
        if (!document.getElementById('dark_mode_css')) {
            let css = `
                html, body {
                    background: #111 !important;
                    filter: invert(1) hue-rotate(180deg) !important;
                }
                img, video, canvas {
                    filter: invert(1) hue-rotate(180deg) !important;
                }
            `;
            let style = document.createElement('style');
            style.id = "dark_mode_css";
            style.innerText = css;
            document.head.appendChild(style);
        }
        """
        web.page().runJavaScript(js)

    def init_hotkeys(self):
        # Focus address bar
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_urlbar)

        # New tab
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_tab(HOME_PAGE))

        # Close tab
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)

        # Reload
        QShortcut(QKeySequence("Ctrl+R"), self, lambda: self.current().reload())
        QShortcut(QKeySequence("F5"), self, lambda: self.current().reload())

        # Back/Forward
        QShortcut(QKeySequence("Alt+Left"), self, lambda: self.current().back())
        QShortcut(QKeySequence("Alt+Right"), self, lambda: self.current().forward())

        # Zoom
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)

        # Dark mode toggle
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_dark_mode)

        # Home
        QShortcut(QKeySequence("Ctrl+H"), self, self.go_home)

    def focus_urlbar(self):
        self.urlbar.setFocus()
        self.urlbar.selectAll()

    def close_current_tab(self):
        idx = self.tabs.currentIndex()
        self.close_tab(idx)


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
