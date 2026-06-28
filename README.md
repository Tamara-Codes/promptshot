# PromptShot

A tiny Windows tool for marking up your screen and pasting an **annotated screenshot**
straight into a chat with an AI coding assistant (or anywhere else).

Press a hotkey, the screen dims slightly, you scribble red marks over whatever you want to
point at, hit **Enter**, and a clean full-colour screenshot — with your marks burned in — is
on the clipboard, ready to `Ctrl+V` into your prompt.

```
Ctrl+Alt+J   →   dim live screen   →   draw   →   Enter   →   screenshot on clipboard
                                                    Esc     →   cancel
```

### Why it exists

When you ask an AI to "align this", "fix this angle", or "move that button", a screenshot
with an arrow on it says it in one shot. Existing tools either **freeze** the screen
(ZoomIt) or pop up a heavy editor afterwards (ShareX, Epic Pen). PromptShot does neither —
the desktop stays **live** underneath while you draw, and the dim overlay never ends up in
the saved image.

## Requirements

- **Windows** (uses the Windows clipboard and screen-grab APIs — does not work under WSL or
  on macOS/Linux).
- **Python 3.9+** for Windows ([python.org](https://www.python.org/downloads/windows/) or
  the Microsoft Store build).

## Install

```powershell
git clone https://github.com/<your-username>/promptshot.git
cd promptshot
python -m pip install -r requirements.txt
```

Dependencies are just **Pillow** (screenshot + draw) and **pywin32** (clipboard). There is
**no global keystroke hook** — the hotkey is a single chord registered with the Win32
`RegisterHotKey` API, so the tool never watches what you type (and won't trip antivirus
keylogger heuristics).

## Usage

### Resident daemon (recommended) — instant hotkey

```powershell
pythonw promptshot_daemon.pyw
```

Runs invisibly in the background with Python and its libraries already loaded, so the
overlay appears **instantly** when you press the hotkey. Use `pythonw` (not `python`) so
there's no console window.

- **Ctrl+Alt+J** — open the draw overlay
- **Draw** with the left mouse button
- **Enter** — copy the annotated screenshot to the clipboard and close
- **Esc** — cancel

### Single-shot fallback — no background process

```powershell
pythonw promptshot.pyw
```

Opens the overlay once and exits after you press Enter/Esc. No hotkey of its own — bind it
to a shortcut key yourself if you like. Handy if you don't want a resident process.

## Start automatically on login (daemon)

1. Press `Win+R`, type `shell:startup`, press Enter — this opens your Startup folder.
2. Right-click → **New → Shortcut**, and for the target use the **full path** to `pythonw`
   plus the script, e.g.:

   ```
   "C:\Path\To\pythonw.exe" "C:\Path\To\promptshot\promptshot_daemon.pyw"
   ```

> **Microsoft Store Python gotcha:** the bare `python` / `pythonw` commands only resolve
> inside a real shell (via the Store app-execution alias). Shortcuts launched from Explorer
> must use the **full** `pythonw.exe` path or they silently do nothing. Find it with
> `where.exe pythonw` (or `(Get-Command pythonw).Source` in PowerShell).

## Configuration

Edit the constants near the top of either script:

| Constant     | Default     | Meaning                                        |
|--------------|-------------|------------------------------------------------|
| `PEN_COLOR`  | `"#ff0000"` | Colour of your marks                           |
| `PEN_WIDTH`  | `4`         | Stroke width in pixels                         |
| `DIM_LEVEL`  | `0.40`      | Overlay dimness (0.0 = invisible, 1.0 = black) |

To **rebind the hotkey** (daemon), change `MODIFIERS` and `VK_KEY` near the top of
`promptshot_daemon.pyw`. `VK_KEY` is a Windows
[virtual-key code](https://learn.microsoft.com/windows/win32/inputdev/virtual-key-codes)
(`0x4A` is `J`); `MODIFIERS` ORs together `MOD_CONTROL`, `MOD_ALT`, `MOD_SHIFT`, `MOD_WIN`.

## How it works

The overlay is a fullscreen semi-transparent tkinter window (`-alpha 0.40`, topmost) that
catches the mouse but lets the live desktop show through. Strokes are stored as line
segments. On **Enter**, the overlay is hidden, `Pillow.ImageGrab.grab()` captures the
**clean** screen, the stored strokes are re-painted onto it crisply with `ImageDraw`
(scaled for high-DPI), and the result is placed on the clipboard as a `CF_DIB`. The dim
layer is never part of the captured image.

## Building a standalone .exe (optional)

If you want to hand this to non-developers who don't have Python, bundle it with
[PyInstaller](https://pyinstaller.org/):

```powershell
python -m pip install pyinstaller
pyinstaller --noconsole --onedir --name PromptShot promptshot_daemon.pyw
```

Use `--onedir` (a folder you zip), **not** `--onefile` — single-file exes self-extract on
every launch and draw more antivirus heuristic attention. The build lands in `dist/`. Note
that an unsigned `.exe` will show a Windows SmartScreen "unknown publisher" prompt the first
time it runs; code-signing removes that but requires a paid certificate.

## License

[MIT](LICENSE) — do whatever you like with it.
