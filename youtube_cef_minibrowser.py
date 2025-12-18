# youtube_cef_minibrowser.py
# Minimal YouTube MiniBrowser using cefpython3 (CEF)
# Features:
# - CEF (Chromium) backend -> much smoother YouTube playback than QWebEngine
# - Basic toolbar (Back, Forward, Reload, Home), address bar, zoom in/out/reset
# - Set user agent (attempt to prefer H.264)
# - Some Chromium flags to reduce preload / trackers that may harm performance
#
# Install: pip install cefpython3
# Run: python youtube_cef_minibrowser.py

import os
import sys
import platform
from cefpython3 import cefpython as cef
import tkinter as tk
from tkinter import ttk

HOME_URL = "https://www.youtube.com/"

# ---------- CEF Init flags ----------
def set_chromium_flags():
    """
    Tweak Chromium command-line flags via environment or cef.CommandLine.
    These are best-effort hints (cannot guarantee server returns H.264).
    """
    # Example flags that can help stability / reduce preload
    flags = [
        "--disable-features=SpareRendererForSitePerProcess,Translate,HeavyAdIntervention",
        "--autoplay-policy=user-gesture-required",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-client-side-phishing-detection",
        "--disable-component-update",
        "--disable-domain-reliability",
        "--disable-webgl",
        "--disable-gpu-compositing",
        "--enable-low-end-device-mode",
        # try to prefer H.264 by limiting webm? not guaranteed:
        # "--enable-features=UsePlatformDecoderForH264", # platform dependent
    ]
    # append flags to QTWEBENGINE_CHROMIUM_FLAGS (some platforms look at env)
    existing = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    if existing:
        existing += " "
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = existing + " ".join(flags)

# ---------- UI with tkinter embedding CEF ----------
class BrowserFrame(tk.Frame):
    def __init__(self, master, initial_url=HOME_URL):
        tk.Frame.__init__(self, master)
        self.master = master
        self.browser = None
        self.initial_url = initial_url

        # Toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)

        self.back_btn = ttk.Button(self.toolbar, text="◀", width=3, command=self.go_back)
        self.back_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.forward_btn = ttk.Button(self.toolbar, text="▶", width=3, command=self.go_forward)
        self.forward_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.reload_btn = ttk.Button(self.toolbar, text="⟳", width=3, command=self.reload)
        self.reload_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.home_btn = ttk.Button(self.toolbar, text="🏠", width=3, command=self.go_home)
        self.home_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # Address bar
        self.address = ttk.Entry(self.toolbar, width=80)
        self.address.pack(side=tk.LEFT, padx=6, pady=3, fill=tk.X, expand=True)
        self.address.bind("<Return>", self.on_address_enter)

        # Zoom controls
        self.zoom_in_btn = ttk.Button(self.toolbar, text="A+", width=3, command=self.zoom_in)
        self.zoom_in_btn.pack(side=tk.LEFT, padx=2)
        self.zoom_out_btn = ttk.Button(self.toolbar, text="A-", width=3, command=self.zoom_out)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=2)
        self.zoom_reset_btn = ttk.Button(self.toolbar, text="A0", width=3, command=self.zoom_reset)
        self.zoom_reset_btn.pack(side=tk.LEFT, padx=2)

        # Browser container
        self.browser_frame = tk.Frame(self)
        self.browser_frame.pack(fill=tk.BOTH, expand=True)

        # Initialize CEF browser after embedding frame is ready
        self.after(10, self.embed_browser)

    def embed_browser(self):
        # On Windows, you must get window handle (HWND); on Linux/Mac it's similar
        window_info = cef.WindowInfo()
        rect = [0, 0, self.browser_frame.winfo_width() or 800, self.browser_frame.winfo_height() or 600]
        # Obtain the window handle depending on platform
        if platform.system() == "Windows":
            hwnd = self.browser_frame.winfo_id()
            window_info.SetAsChild(hwnd, rect)
        else:
            # For Linux and macOS, SetAsChild tends to work as well
            handle = self.browser_frame.winfo_id()
            window_info.SetAsChild(handle, rect)

        # Browser settings
        browser_settings = {
            "plugins": False,
            "windowless_frame_rate": 30,  # reduce render frequency
        }

        # Create browser
        self.browser = cef.CreateBrowserSync(window_info,
                                             settings=browser_settings,
                                             url=self.initial_url)
        # Set custom user agent to increase chance of H.264 selection
        # (server chooses codecs/manifest partly based on UA; not guaranteed)
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36")
        self.browser.SetUserAgent(ua)

        # Bind python functions to JS if needed (not used here)
        self.set_client_handlers()
        # Update address bar when URL changes
        self.browser.SetClientHandler(LoadHandler(self.on_load_state_change))
        # initial zoom factor
        self.zoom_level = 0  # CEF uses zoom level (0 default)
        self.apply_zoom()

    def set_client_handlers(self):
        # Optionally set handlers (RequestHandler etc.) to block trackers or codecs.
        # You can implement a RequestHandler and call cef.SetGlobalClientHandler, but keep minimal for stability.
        pass

    # toolbar actions
    def go_back(self):
        if self.browser and self.browser.CanGoBack():
            self.browser.GoBack()

    def go_forward(self):
        if self.browser and self.browser.CanGoForward():
            self.browser.GoForward()

    def reload(self):
        if self.browser:
            self.browser.Reload()

    def go_home(self):
        if self.browser:
            self.browser.LoadUrl(HOME_URL)

    def on_address_enter(self, event=None):
        url = self.address.get().strip()
        if not url:
            return
        if not url.startswith("http"):
            url = "https://" + url
        if self.browser:
            self.browser.LoadUrl(url)

    def zoom_in(self):
        self.zoom_level = min(self.zoom_level + 1, 9)
        self.apply_zoom()

    def zoom_out(self):
        self.zoom_level = max(self.zoom_level - 1, -9)
        self.apply_zoom()

    def zoom_reset(self):
        self.zoom_level = 0
        self.apply_zoom()

    def apply_zoom(self):
        if self.browser:
            self.browser.SetZoomLevel(self.zoom_level)

    def on_load_state_change(self, browser, frame, url, loaded):
        # callback to update address bar
        if browser == self.browser:
            try:
                self.address.delete(0, tk.END)
                self.address.insert(0, url)
            except Exception:
                pass

# simple load handler to capture url changes
class LoadHandler(object):
    def __init__(self, callback):
        self.callback = callback

    def OnLoadingStateChange(self, browser, is_loading, **_):
        # called on loading start/stop; we can update address from browser.GetUrl()
        if not is_loading:
            try:
                url = browser.GetUrl()
                self.callback(browser, None, url, True)
            except Exception:
                pass

# ---------- Main app ----------
def main():
    # Chromium flags
    set_chromium_flags()

    # CEF initialize
    cef_settings = {
        "cache_path": "",  # empty -> in-memory cache
        "persist_session_cookies": False,
        "ignore_certificate_errors": True,
        # optionally log to file for debugging:
        # "log_file": "cef.log",
    }
    cef.Initialize(settings=cef_settings)

    # Tkinter main window
    root = tk.Tk()
    root.title("YouTube MiniBrowser (CEF) — Ultra Smooth")
    root.geometry("1200x800")

    frame = BrowserFrame(root, initial_url=HOME_URL)
    frame.pack(fill=tk.BOTH, expand=True)

    # integrate CEF message loop with Tkinter
    # periodically call cef.MessageLoopWork
    def loop_work():
        cef.MessageLoopWork()
        root.after(10, loop_work)  # 10ms tick

    root.after(10, loop_work)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def on_close(root):
    # Must shutdown CEF before exiting
    cef.Shutdown()
    root.destroy()
    sys.exit(0)

if __name__ == "__main__":
    main()
