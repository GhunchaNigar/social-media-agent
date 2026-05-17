"""
AI Social Media Agent — Windows Launcher
Double-click to start. Opens automatically in your browser.
"""

import sys
import os
import time
import socket
import threading
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

# ── Resolve paths whether running as .exe or .py ──────────────────────────────
if getattr(sys, "frozen", False):
    # Running as PyInstaller EXE — base dir is temp _MEIPASS
    BASE_DIR    = sys._MEIPASS
    # App files sit next to the EXE
    APP_DIR     = os.path.join(os.path.dirname(sys.executable), "app")
    PYTHON_EXE  = os.path.join(os.path.dirname(sys.executable), "python", "python.exe")
else:
    BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
    APP_DIR     = os.path.join(BASE_DIR, "app")
    PYTHON_EXE  = sys.executable

APP_SCRIPT  = os.path.join(APP_DIR, "social_media_agent.py")
PORT        = 8501


# ── Check if port is free ──────────────────────────────────────────────────────
def port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def find_free_port(start=8501):
    for p in range(start, start + 20):
        if port_free(p):
            return p
    return start


# ── Wait until Streamlit is up ─────────────────────────────────────────────────
def wait_for_server(port, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not port_free(port):
            return True
        time.sleep(0.5)
    return False


# ── Launcher GUI ───────────────────────────────────────────────────────────────
class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Social Media Agent")
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(bg="#0f1117")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._proc   = None
        self._port   = find_free_port()
        self._thread = None

        # ── UI ──
        tk.Label(self, text="🚀  AI Social Media Agent",
                 font=("Segoe UI", 16, "bold"),
                 fg="white", bg="#0f1117").pack(pady=(28, 4))

        tk.Label(self, text="Powered by Gemini AI · SEO · Digital Marketing",
                 font=("Segoe UI", 9), fg="#888", bg="#0f1117").pack()

        self._status = tk.StringVar(value="Starting server…")
        tk.Label(self, textvariable=self._status,
                 font=("Segoe UI", 10), fg="#4fc3f7", bg="#0f1117").pack(pady=10)

        self._bar = ttk.Progressbar(self, mode="indeterminate", length=340)
        self._bar.pack(pady=4)
        self._bar.start(12)

        self._btn = tk.Button(
            self, text="Open in Browser", state="disabled",
            font=("Segoe UI", 10, "bold"),
            bg="#1877f2", fg="white", relief="flat",
            padx=18, pady=6,
            command=self._open_browser,
        )
        self._btn.pack(pady=14)

        self._start_server()

    # ── Start Streamlit in background thread ───────────────────────────────────
    def _start_server(self):
        def run():
            streamlit_cmd = [
                PYTHON_EXE, "-m", "streamlit", "run",
                APP_SCRIPT,
                f"--server.port={self._port}",
                "--server.headless=true",
                "--browser.gatherUsageStats=false",
                "--server.enableCORS=false",
            ]
            try:
                self._proc = subprocess.Popen(
                    streamlit_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=APP_DIR,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                )
            except FileNotFoundError:
                self.after(0, lambda: self._status.set("❌ Python/Streamlit not found. See README."))
                return

            if wait_for_server(self._port, timeout=90):
                self.after(0, self._on_ready)
            else:
                self.after(0, lambda: self._status.set("❌ Server failed to start. Check README."))

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def _on_ready(self):
        self._bar.stop()
        self._bar.configure(mode="determinate", value=100)
        self._status.set(f"✅  Running at  localhost:{self._port}")
        self._btn.configure(state="normal")
        self._open_browser()

    def _open_browser(self):
        webbrowser.open(f"http://localhost:{self._port}")

    def on_close(self):
        if self._proc:
            self._proc.terminate()
        self.destroy()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
