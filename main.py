#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

HOME_PAGE = "https://www.google.com"

class BrowserTab(QWidget):
    def __init__(self, url=HOME_PAGE):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl(url))
        self.layout.addWidget(self.webview)
        self.setLayout(self.layout)

class MiniBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Browser")
        self.resize(1100, 700)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_from_tab)
        self.setCentralWidget(self.tabs)

        # Toolbar
        self.navtb = QToolBar("Navigation")
        self.addToolBar(self.navtb)

        back_btn = QAction("◀", self)
        back_btn.setStatusTip("Back")
        back_btn.triggered.connect(self.go_back)
        self.navtb.addAction(back_btn)

        forward_btn = QAction("▶", self)
        forward_btn.setStatusTip("Forward")
        forward_btn.triggered.connect(self.go_forward)
        self.navtb.addAction(forward_btn)

        reload_btn = QAction("⟳", self)
        reload_btn.setStatusTip("Reload")
        reload_btn.triggered.connect(self.reload_page)
        self.navtb.addAction(reload_btn)

        home_btn = QAction("🏠", self)
        home_btn.setStatusTip("Home")
        home_btn.triggered.connect(self.go_home)
        self.navtb.addAction(home_btn)

        self.navtb.addSeparator()

        # Address bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.navtb.addWidget(self.urlbar)

        # New tab action
        new_tab_action = QAction("+", self)
        new_tab_action.setStatusTip("New Tab")
        new_tab_action.triggered.connect(self.add_new_tab)
        self.navtb.addAction(new_tab_action)

        # Add an initial tab
        self.add_new_tab(QUrl(HOME_PAGE), switch_to=True)

        # Shortcuts
        self.urlbar.setPlaceholderText("Nhập URL hoặc từ khóa rồi Enter (ví dụ: github hoặc https://example.com)")
        self.show()

    def add_new_tab(self, qurl=None, switch_to=True):
        if qurl is None:
            url = HOME_PAGE
        elif isinstance(qurl, QUrl):
            url = qurl.toString()
        else:
            url = qurl

        new_tab = BrowserTab(url=url)
        i = self.tabs.addTab(new_tab, "Mới")
        # update tab title when page loads
        new_tab.webview.titleChanged.connect(lambda title, tab_index=i: self.tabs.setTabText(tab_index, title[:40] or "Mới"))
        new_tab.webview.urlChanged.connect(lambda q, tab_index=i: self.on_url_changed(q, tab_index))
        if switch_to:
            self.tabs.setCurrentIndex(i)

    def close_tab(self, index):
        if self.tabs.count() < 2:
            # confirm exit
            choice = QMessageBox.question(self, "Thoát", "Đóng tab cuối cùng sẽ thoát. Bạn có muốn thoát?",
                                          QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                QApplication.quit()
            return
        self.tabs.removeTab(index)

    def current_webview(self) -> QWebEngineView:
        widget = self.tabs.currentWidget()
        if widget:
            return widget.webview
        return None

    def navigate_to_url(self):
        text = self.urlbar.text().strip()
        if not text:
            return
        url = self.guess_url(text)
        webview = self.current_webview()
        if webview:
            webview.setUrl(QUrl(url))

    def guess_url(self, text: str) -> str:
        # Nếu có schema thì giữ nguyên, nếu không, kiểm tra dạng like domain, else search
        if text.startswith("http://") or text.startswith("https://"):
            return text
        if "." in text and " " not in text:
            # đơn giản thêm http
            return "http://" + text
        # else: search on Google
        from urllib.parse import quote_plus
        return "https://www.google.com/search?q=" + quote_plus(text)

    def go_back(self):
        w = self.current_webview()
        if w and w.history().canGoBack():
            w.back()

    def go_forward(self):
        w = self.current_webview()
        if w and w.history().canGoForward():
            w.forward()

    def reload_page(self):
        w = self.current_webview()
        if w:
            w.reload()

    def go_home(self):
        w = self.current_webview()
        if w:
            w.setUrl(QUrl(HOME_PAGE))

    def on_url_changed(self, qurl: QUrl, tab_index: int):
        # nếu tab hiện tại thay đổi url thì cập nhật urlbar
        if tab_index == self.tabs.currentIndex():
            self.urlbar.setText(qurl.toString())

    def update_url_from_tab(self, index: int):
        w = self.current_webview()
        if w:
            self.urlbar.setText(w.url().toString())
        else:
            self.urlbar.setText("")

def main():
    app = QApplication(sys.argv)
    # cần gọi để khởi tạo QWebEngine
    browser = MiniBrowser()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
