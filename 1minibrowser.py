import sys
import json
import re
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

HOME_PAGE = "https://www.google.com"

# --------------------------
#  AD BLOCK INTERCEPTOR
# --------------------------
class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
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
                print(f"⛔ BLOCKED: {url}")
                return

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
        self.setWindowTitle("MiniBrowser (AdBlock)")
        self.resize(1100, 700)

        # --- PROFILE + ADBLOCK ---
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setRequestInterceptor(AdBlockInterceptor())
        self.profile.downloadRequested.connect(self.on_download_requested)

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
        self.dark_btn.triggered.connect(self.toggle_dark_mode)
        nav.addAction(self.dark_btn)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        nav.addWidget(self.urlbar)

        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_tab(HOME_PAGE))
        nav.addAction(new_tab_btn)

        # --- Progress bar for download ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.statusBar().addPermanentWidget(self.progress_bar)

        # --- First Tab ---
        self.add_tab(HOME_PAGE)

        # --- Start download manager process ---
        self.download_process = subprocess.Popen(
            [sys.executable, "1download_manager.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True
        )
        # read stdout in background thread
        self.download_thread = QThread()
        worker = Worker(self.download_process.stdout)
        worker.moveToThread(self.download_thread)
        self.download_thread.started.connect(worker.run)
        worker.progress_signal.connect(self.update_progress)
        self.download_thread.start()

    # --------------------------
    #  TABS / NAVIGATION
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
                    html, body { background: #111 !important; filter: invert(1) hue-rotate(180deg) !important; }
                    img, video, canvas { filter: invert(1) hue-rotate(180deg) !important; }
                `;
                let style = document.createElement('style'); style.id = "dark_mode_css"; style.innerText = css;
                document.head.appendChild(style);
            })();
            """
            self.dark_btn.setText("☀")
        else:
            js = """
            (function() {
                let style = document.getElementById("dark_mode_css");
                if(style) style.remove();
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
                html, body { background: #111 !important; filter: invert(1) hue-rotate(180deg) !important; }
                img, video, canvas { filter: invert(1) hue-rotate(180deg) !important; }
            `;
            let style = document.createElement('style'); style.id = "dark_mode_css"; style.innerText = css;
            document.head.appendChild(style);
        }
        """
        web.page().runJavaScript(js)

    # --------------------------
    #  DOWNLOAD
    # --------------------------
    def on_download_requested(self, download):
        url = download.url().toString()
        path, _ = QFileDialog.getSaveFileName(self, "Save As", download.downloadFileName())
        if not path:
            download.cancel()
            return
        download.cancel()
        # gửi lệnh download manager
        data = {"url": url, "path": path}
        self.download_process.stdin.write(json.dumps(data)+"\n")
        self.download_process.stdin.flush()

    def update_progress(self, index, progress, status=None):
        self.progress_bar.setValue(progress)
        if status == "completed":
            QMessageBox.information(self, "Download Complete", f"File download completed.")

# --------------------------
#  Worker Thread for reading download_manager stdout
# --------------------------
class Worker(QObject):
    progress_signal = pyqtSignal(int, int, str)  # index, progress, status

    def __init__(self, stdout):
        super().__init__()
        self.stdout = stdout

    def run(self):
        for line in self.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                index = data.get("index", 0)
                progress = data.get("progress", 0)
                status = data.get("status", None)
                self.progress_signal.emit(index, progress, status)
            except Exception as e:
                print("Worker parse error:", e)

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
