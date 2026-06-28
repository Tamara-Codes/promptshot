# promptshot.pyw — single-shot version. Launch it (e.g. from a shortcut) -> draw on a
# slightly-dimmed live screen -> Enter copies a CLEAN full-colour screenshot (with your
# red marks) to the clipboard -> Esc cancels. No freeze: the desktop stays live underneath.
#
# This is the no-daemon fallback: it has NO hotkey and NO background process — it just runs
# once and exits. Bind it to a shortcut key yourself, or use promptshot_daemon.pyw for the
# instant Ctrl+Alt+J experience.
#
# Run with WINDOWS python (not WSL). One-time: pip install -r requirements.txt

import io
import time
import ctypes
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

root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.attributes("-alpha", DIM_LEVEL)   # dim, semi-transparent layer that DOES catch the mouse
root.config(cursor="crosshair", bg="black")

canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

strokes = []                            # remembered so we can redraw them crisp on the clean grab
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


def copy_to_clipboard(img):
    out = io.BytesIO()
    img.convert("RGB").save(out, "BMP")
    data = out.getvalue()[14:]          # strip 14-byte BMP header -> CF_DIB
    out.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def capture(_=None):
    cw, ch = canvas.winfo_width(), canvas.winfo_height()
    root.withdraw()                     # hide the dim layer so we grab the CLEAN screen
    root.update()
    time.sleep(0.12)                    # let the desktop repaint
    img = ImageGrab.grab()
    sx, sy = img.width / cw, img.height / ch
    draw = ImageDraw.Draw(img)
    for x0, y0, x1, y1 in strokes:      # paint your marks back on, full-colour and crisp
        draw.line((x0 * sx, y0 * sy, x1 * sx, y1 * sy),
                  fill=(255, 0, 0), width=max(2, int(PEN_WIDTH * sx)))
    copy_to_clipboard(img)
    root.destroy()


def cancel(_=None):
    root.destroy()


root.bind("<Return>", capture)
root.bind("<Escape>", cancel)

root.focus_force()
root.mainloop()
