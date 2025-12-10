import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

HOME_PAGE = "https://www.google.com"

# --------------------------
#  BROWSER TAB
# --------------------------
class BrowserTab(QWidget):
    def __init__(self, url=HOME_PAGE, profile=None):
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
        self.dark_mode = False
        self.setWindowTitle("MiniBrowser")
        self.resize(1100, 700)

        # --- PROFILE ---
        self.profile = QWebEngineProfile("MiniBrowserProfile", self)
        self.profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_urlbar)
        self.setCentralWidget(self.tabs)

        # --- Toolbar ---
        nav = QToolBar("Navigation")
        self.addToolBar(nav)

        # Back / Forward / Reload / Home
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
        nav.addSeparator()

        # Dark mode
        self.dark_btn = QAction("🌙", self)
        self.dark_btn.setStatusTip("Toggle Dark Mode")
        self.dark_btn.triggered.connect(self.toggle_dark_mode)
        nav.addAction(self.dark_btn)

        # URL bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        nav.addWidget(self.urlbar)

        # New tab
        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_tab(HOME_PAGE))
        nav.addAction(new_tab_btn)

        # --- Hotkeys ---
        self.init_hotkeys()

        # --- Download manager ---
        self.profile.downloadRequested.connect(self.on_download_requested)

        # --- First Tab ---
        self.add_tab(HOME_PAGE)

    # --------------------------
    #  ADD / CLOSE TAB
    # --------------------------
    def add_tab(self, url):
        tab = BrowserTab(url, profile=self.profile)
        tab.web.loadFinished.connect(lambda ok, w=tab.web: self.apply_dark_if_enabled(w))
        index = self.tabs.addTab(tab, "Tab")
        tab.web.titleChanged.connect(lambda t, i=index: self.tabs.setTabText(i, t[:30]))
        tab.web.urlChanged.connect(lambda u, i=index: self.url_changed(u, i))
        self.tabs.setCurrentIndex(index)

    def close_tab(self, i):
        if self.tabs.count() == 1:
            self.close()
        else:
            self.tabs.removeTab(i)

    def current(self):
        tab = self.tabs.currentWidget()
        return tab.web if tab else None

    # --------------------------
    #  NAVIGATION
    # --------------------------
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
        w = self.current()
        if w:
            w.setUrl(QUrl(HOME_PAGE))

    # --------------------------
    #  ZOOM
    # --------------------------
    def zoom_in(self):
        w = self.current()
        if w:
            w.setZoomFactor(w.zoomFactor() + 0.1)

    def zoom_out(self):
        w = self.current()
        if w:
            w.setZoomFactor(max(0.2, w.zoomFactor() - 0.1))

    def zoom_reset(self):
        w = self.current()
        if w:
            w.setZoomFactor(1.0)

    # --------------------------
    #  DARK MODE
    # --------------------------
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode

        js = ""
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
            self.dark_btn.setText("☀")
        else:
            js = """
            (function() {
                let style = document.getElementById("dark_mode_css");
                if (style) style.remove();
            })();
            """
            self.dark_btn.setText("🌙")

        w = self.current()
        if w and w.page():
            w.page().runJavaScript(js)

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

    # --------------------------
    #  HOTKEYS
    # --------------------------
    def init_hotkeys(self):
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_urlbar)
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_tab(HOME_PAGE))
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+R"), self, lambda: self.current().reload())
        QShortcut(QKeySequence("F5"), self, lambda: self.current().reload())
        QShortcut(QKeySequence("Alt+Left"), self, lambda: self.current().back())
        QShortcut(QKeySequence("Alt+Right"), self, lambda: self.current().forward())
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_dark_mode)
        QShortcut(QKeySequence("Ctrl+H"), self, self.go_home)

    def focus_urlbar(self):
        self.urlbar.setFocus()
        self.urlbar.selectAll()

    def close_current_tab(self):
        idx = self.tabs.currentIndex()
        self.close_tab(idx)

    # --------------------------
    #  DOWNLOAD MANAGER
    # --------------------------
    def on_download_requested(self, download):
        default_path = download.path()
        path, _ = QFileDialog.getSaveFileName(self, "Save File As", default_path)
        if path:
            download.setPath(path)
            download.accept()
            download.downloadProgress.connect(self.download_progress)
            download.finished.connect(lambda: self.download_finished(download))
        else:
            download.cancel()

    def download_progress(self, received, total):
        if total > 0:
            percent = received * 100 / total
            print(f"Downloading: {percent:.1f}%")

    def download_finished(self, download):
        if download.state() == download.DownloadCompleted:
            QMessageBox.information(self, "Download Complete", f"File saved to:\n{download.path()}")
        elif download.state() == download.DownloadCancelled:
            QMessageBox.warning(self, "Download Cancelled", "Download was cancelled.")
        elif download.state() == download.DownloadInterrupted:
            QMessageBox.critical(self, "Download Failed", "Download interrupted.")

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
