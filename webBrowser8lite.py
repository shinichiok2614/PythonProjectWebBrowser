import sys
import os
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

CONFIG_FILE = "config_light.json"
DEFAULT_HOME = "https://www.google.com"

# --------------------------
#  BROWSER TAB
# --------------------------
class BrowserTab(QWidget):
    def __init__(self, url=DEFAULT_HOME, profile=None, zoom_factor=1.0):
        super().__init__()
        layout = QVBoxLayout(self)
        self.web = QWebEngineView()
        if profile:
            page = QWebEnginePage(profile, self.web)
            self.web.setPage(page)
        self.web.setUrl(QUrl(url))
        self.web.setZoomFactor(zoom_factor)
        layout.addWidget(self.web)
        self.setLayout(layout)

# --------------------------
#  MINI BROWSER
# --------------------------
class MiniBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.load_config()

        self.zoom_data = self.config.get("zoom_data", {})  # host -> zoom factor
        self.bookmarks = self.config.get("bookmarks", [])

        self.setWindowTitle("MiniBrowser Light")
        self.resize(1100, 700)

        # --- PROFILE ---
        self.profile = QWebEngineProfile("LightProfile", self)
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

        # URL bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate)
        nav.addWidget(self.urlbar)

        # New tab
        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_tab(DEFAULT_HOME))
        nav.addAction(new_tab_btn)

        # Bookmark button
        bookmark_btn = QAction("🔖", self)
        bookmark_btn.triggered.connect(self.manage_bookmarks)
        nav.addAction(bookmark_btn)

        # Hotkeys
        self.init_hotkeys()

        # First tab
        self.add_tab(DEFAULT_HOME)

    # --------------------------
    # CONFIG
    # --------------------------
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def save_config(self):
        self.config["zoom_data"] = self.zoom_data
        self.config["bookmarks"] = self.bookmarks
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    # --------------------------
    # TAB MANAGEMENT
    # --------------------------
    def add_tab(self, url):
        host = QUrl(url).host()
        zoom = self.zoom_data.get(host, 1.0)
        tab = BrowserTab(url, profile=self.profile, zoom_factor=zoom)
        index = self.tabs.addTab(tab, "Tab")
        tab.web.titleChanged.connect(lambda t, i=index: self.tabs.setTabText(i, t[:30]))
        tab.web.urlChanged.connect(lambda u, i=index: self.url_changed(u, i))
        tab.web.urlChanged.connect(lambda u, w=tab.web: self.apply_saved_zoom(u, w))
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
    # NAVIGATION
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
            w.setUrl(QUrl(DEFAULT_HOME))

    # --------------------------
    # ZOOM
    # --------------------------
    def apply_saved_zoom(self, url, web):
        host = QUrl(url).host()
        zoom = self.zoom_data.get(host, 1.0)
        web.setZoomFactor(zoom)

    def zoom_in(self):
        w = self.current()
        if w:
            f = w.zoomFactor() + 0.1
            w.setZoomFactor(f)
            host = w.url().host()
            self.zoom_data[host] = f
            self.save_config()

    def zoom_out(self):
        w = self.current()
        if w:
            f = max(0.2, w.zoomFactor() - 0.1)
            w.setZoomFactor(f)
            host = w.url().host()
            self.zoom_data[host] = f
            self.save_config()

    def zoom_reset(self):
        w = self.current()
        if w:
            w.setZoomFactor(1.0)
            host = w.url().host()
            self.zoom_data[host] = 1.0
            self.save_config()

    # --------------------------
    # HOTKEYS
    # --------------------------
    def init_hotkeys(self):
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_urlbar)
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.add_tab(DEFAULT_HOME))
        QShortcut(QKeySequence("Ctrl+W"), self, self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+R"), self, lambda: self.current().reload())
        QShortcut(QKeySequence("F5"), self, lambda: self.current().reload())
        QShortcut(QKeySequence("Alt+Left"), self, lambda: self.current().back())
        QShortcut(QKeySequence("Alt+Right"), self, lambda: self.current().forward())
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.zoom_reset)
        QShortcut(QKeySequence("Ctrl+B"), self, self.manage_bookmarks)

    def focus_urlbar(self):
        self.urlbar.setFocus()
        self.urlbar.selectAll()

    def close_current_tab(self):
        idx = self.tabs.currentIndex()
        self.close_tab(idx)

    # --------------------------
    # BOOKMARKS
    # --------------------------
    def manage_bookmarks(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Bookmarks")
        dlg.resize(500, 400)
        layout = QVBoxLayout(dlg)

        self.bookmark_tree = QTreeWidget()
        self.bookmark_tree.setHeaderLabels(["Title", "URL"])
        layout.addWidget(self.bookmark_tree)

        self.populate_bookmark_tree()
        self.bookmark_tree.itemDoubleClicked.connect(self.open_bookmark)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Current")
        add_btn.clicked.connect(self.add_bookmark)
        btn_layout.addWidget(add_btn)
        del_btn = QPushButton("Delete Selected")
        del_btn.clicked.connect(self.delete_bookmark)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)

        dlg.exec_()

    def populate_bookmark_tree(self):
        self.bookmark_tree.clear()
        groups = {}
        for bm in self.bookmarks:
            domain = QUrl(bm['url']).host()
            if domain not in groups:
                group_item = QTreeWidgetItem([domain])
                self.bookmark_tree.addTopLevelItem(group_item)
                groups[domain] = group_item
            child = QTreeWidgetItem([bm['title'], bm['url']])
            groups[domain].addChild(child)

    def add_bookmark(self):
        w = self.current()
        if not w:
            return
        url = w.url().toString()
        title = w.title() or url
        if any(b['url'] == url for b in self.bookmarks):
            return
        self.bookmarks.append({"title": title, "url": url})
        self.save_config()
        self.populate_bookmark_tree()

    def delete_bookmark(self):
        item = self.bookmark_tree.currentItem()
        if item and item.childCount() == 0:
            url = item.text(1)
            self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
            self.save_config()
            parent = item.parent()
            if parent:
                parent.removeChild(item)

    def open_bookmark(self, item, column):
        if item.childCount() == 0:
            self.add_tab(item.text(1))

# --------------------------
# RUN APP
# --------------------------
def main():
    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)
    app = QApplication(sys.argv)
    browser = MiniBrowser()
    browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
