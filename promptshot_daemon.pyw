# promptshot_daemon.pyw — stays running in the background with Python and its libraries
# already loaded, so pressing the hotkey shows the overlay INSTANTLY (no per-press startup tax).
#
# Hotkey: Ctrl+Alt+J -> dim the live screen -> draw red marks -> Enter copies a clean
# full-colour screenshot (with your marks) to the clipboard -> Esc cancels. Then Ctrl+V.
#
# The hotkey uses the Win32 RegisterHotKey API (a single registered chord), NOT a global
# keystroke hook — so it does not watch everything you type and won't trip antivirus
# keylogger heuristics.
#
# Run with WINDOWS pythonw (not WSL). One-time: pip install -r requirements.txt

import io
import time
import queue
import ctypes
from ctypes import wintypes
import threading
import tkinter as tk
from PIL import ImageGrab, ImageDraw
import win32clipboard

# Crisp grab on high-DPI displays.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

PEN_COLOR = "#ff0000"   # colour of your on-screen marks
PEN_WIDTH = 4           # stroke width in pixels
DIM_LEVEL = 0.40        # 0.0 = invisible overlay, 1.0 = opaque black

# --- Hotkey definition (Ctrl+Alt+J). Change MODIFIERS / VK_KEY to rebind. ---
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
MODIFIERS = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
VK_KEY = 0x4A           # 'J' (virtual-key code)

root = tk.Tk()
root.withdraw()                 # the daemon itself never shows a window
_events = queue.Queue()
_busy = {"on": False}


def copy_to_clipboard(img):
    out = io.BytesIO()
    img.convert("RGB").save(out, "BMP")
    data = out.getvalue()[14:]          # strip 14-byte BMP header -> CF_DIB
    out.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def show_overlay():
    if _busy["on"]:                     # ignore extra presses while one is open
        return
    _busy["on"] = True

    win = tk.Toplevel(root)
    win.attributes("-fullscreen", True)
    win.attributes("-topmost", True)
    win.attributes("-alpha", DIM_LEVEL)
    win.config(cursor="crosshair", bg="black")
    canvas = tk.Canvas(win, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    strokes = []                        # remembered so we can redraw them crisp on the clean grab
    last = {"x": 0, "y": 0}

    def on_press(e):
        last["x"], last["y"] = e.x, e.y

    def on_drag(e):
        canvas.create_line(last["x"], last["y"], e.x, e.y,
                           fill=PEN_COLOR, width=PEN_WIDTH,
                           capstyle="round", smooth=True)
        strokes.append((last["x"], last["y"], e.x, e.y))
        last["x"], last["y"] = e.x, e.y

    canvas.bind("<Button-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)

    def close():
        _busy["on"] = False
        win.destroy()

    def capture(_=None):
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        win.withdraw()                  # hide the dim layer -> grab the CLEAN screen
        win.update()
        time.sleep(0.12)                # let the desktop repaint
        img = ImageGrab.grab()
        sx, sy = img.width / cw, img.height / ch
        draw = ImageDraw.Draw(img)
        for x0, y0, x1, y1 in strokes:  # paint your marks back on, full-colour and crisp
            draw.line((x0 * sx, y0 * sy, x1 * sx, y1 * sy),
                      fill=(255, 0, 0), width=max(2, int(PEN_WIDTH * sx)))
        copy_to_clipboard(img)
        close()

    win.bind("<Return>", capture)
    win.bind("<Escape>", lambda _=None: close())
    win.focus_force()


def poll():
    """Runs on the tkinter (main) thread: drains hotkey presses into overlays."""
    try:
        while True:
            _events.get_nowait()
            show_overlay()
    except queue.Empty:
        pass
    root.after(40, poll)


def hotkey_thread():
    """Registers Ctrl+Alt+J and pumps a Win32 message loop on its own thread.

    RegisterHotKey with hWnd=None posts WM_HOTKEY to THIS thread's message queue,
    so registration and the GetMessage loop must live on the same thread.
    """
    user32 = ctypes.windll.user32
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int,
                                      wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG),
                                   wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = ctypes.c_int

    if not user32.RegisterHotKey(None, 1, MODIFIERS, VK_KEY):
        # Most likely another app (or a second copy of this daemon) already owns the chord.
        return

    msg = wintypes.MSG()
    while True:
        ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
        if ret in (0, -1):              # 0 = WM_QUIT, -1 = error -> stop
            break
        if msg.message == WM_HOTKEY:
            _events.put(1)
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


threading.Thread(target=hotkey_thread, daemon=True).start()
root.after(40, poll)
root.mainloop()
