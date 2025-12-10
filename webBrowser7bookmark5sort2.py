import sys
import os
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

CONFIG_FILE = "config.json"
DEFAULT_HOME = "https://www.google.com"
SKIP_DARK_MODE = ["youtube.com", "twitter.com", "facebook.com"]  # Các trang nặng bỏ dark mode

# --------------------------
#  BROWSER TAB
# --------------------------
class BrowserTab(QWidget):
    def __init__(self, url=DEFAULT_HOME, profile=None):
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
        self.load_config()

        self.dark_mode = self.config.get("dark_mode", False)
        self.home_page = self.config.get("home_page", DEFAULT_HOME)
        self.zoom_factor = self.config.get("zoom_factor", 1.0)

        self.setWindowTitle("MiniBrowser Stable")
        self.resize(1100, 700)

        # --- PROFILE tối ưu ---
        self.profile = QWebEngineProfile("MiniBrowserProfile", self)
        self.profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        self.profile.setHttpCacheMaximumSize(100*1024*1024)  # 100MB cache

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_urlbar)
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

        self.dark_btn = QAction("🌙", self)
        self.dark_btn.setStatusTip("Toggle Dark Mode")
        self.dark_btn.triggered.connect(self.toggle_dark_mode)
        nav.addAction(self.dark_btn)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        nav.addWidget(self.urlbar)

        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_tab(self.home_page))
        nav.addAction(new_tab_btn)

        self.init_hotkeys()

        # Download
        self.profile.downloadRequested.connect(self.on_download_requested)

        # First Tab
        self.add_tab(self.home_page)
        self.apply_zoom()
        self.apply_dark_if_enabled_current()

    # --------------------------
    #  CONFIG
    # --------------------------
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        self.config["dark_mode"] = self.dark_mode
        self.config["home_page"] = self.home_page
        self.config["zoom_factor"] = self.zoom_factor
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    # --------------------------
    #  TAB
    # --------------------------
    def add_tab(self, url):
        tab = BrowserTab(url, profile=self.profile)
        tab.web.loadFinished.connect(lambda ok, w=tab.web: self.apply_dark_if_enabled(w))
        tab.web.loadFinished.connect(lambda ok, w=tab.web: self.apply_zoom_to_tab(w))
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
            w.setUrl(QUrl(self.home_page))

    # --------------------------
    #  ZOOM
    # --------------------------
    def zoom_in(self):
        self.zoom_factor += 0.1
        self.apply_zoom_to_tab(self.current())
        self.save_config()

    def zoom_out(self):
        self.zoom_factor = max(0.2, self.zoom_factor - 0.1)
        self.apply_zoom_to_tab(self.current())
        self.save_config()

    def zoom_reset(self):
        self.zoom_factor = 1.0
        self.apply_zoom_to_tab(self.current())
        self.save_config()

    def apply_zoom(self):
        for i in range(self.tabs.count()):
            self.apply_zoom_to_tab(self.tabs.widget(i).web)

    def apply_zoom_to_tab(self, web):
        if web:
            web.setZoomFactor(self.zoom_factor)

    # --------------------------
    #  DARK MODE
    # --------------------------
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_dark_if_enabled_current()
        self.save_config()

    def apply_dark_if_enabled_current(self):
        web = self.current()
        if web:
            self.apply_dark_if_enabled(web)

    def apply_dark_if_enabled(self, web):
        url = web.url().toString()
        if any(domain in url for domain in SKIP_DARK_MODE):
            return  # Không áp dụng dark mode cho trang nặng

        if not self.dark_mode:
            js_remove = """
            (function() {
                let style = document.getElementById("dark_mode_css");
                if (style) style.remove();
            })();
            """
            web.page().runJavaScript(js_remove)
            self.dark_btn.setText("🌙")
            return

        js = """
        (function() {
            if (!document.getElementById("dark_mode_css")) {
                let css = `
                    html, body { background: #111 !important; }
                `;
                let style = document.createElement('style');
                style.id = "dark_mode_css";
                style.innerText = css;
                document.head.appendChild(style);
            }
        })();
        """
        web.page().runJavaScript(js)
        self.dark_btn.setText("☀")

    # --------------------------
    #  HOTKEYS
    # --------------------------
    def init_hotkeys(self):
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_urlbar)
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_tab(self.home_page))
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
    #  DOWNLOAD
    # --------------------------
    def on_download_requested(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File As", download.path())
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
