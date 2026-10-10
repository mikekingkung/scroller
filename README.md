# scroller

A collection of small pygame projects, including **defender.py** — a
Defender-style arcade game: fly over a horizontally-wrapping planet, shoot
down Landers before they abduct your Humans, rescue anyone dropped mid-air,
and clear each wave.

## Running in VS Code

1. **Open the project folder** in VS Code (`File > Open Folder...` and select
   this `scroller` folder).

2. **Select a Python interpreter.** Open the Command Palette
   (`Ctrl+Shift+P`) and run `Python: Select Interpreter`. Pick your installed
   Python 3 (3.9–3.12 recommended; see the note below for 3.13+).

3. **Create and activate a virtual environment** using the VS Code integrated
   terminal (`` Ctrl+` ``):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   VS Code will usually offer to select the new `.venv` interpreter
   automatically — accept that prompt, or re-run `Python: Select Interpreter`
   and choose `.venv`.

4. **Install dependencies:**

   ```powershell
   pip install pygame
   ```

   > **Note:** on very new Python versions (3.13+), the official `pygame`
   > package may not yet publish a prebuilt wheel, and installing it will
   > try to compile from source and fail. If that happens, install the
   > drop-in-compatible community fork instead:
   > ```powershell
   > pip install pygame-ce
   > ```
   > It's imported the same way (`import pygame`), so no code changes are
   > needed.

5. **Run the game:**
   - Open `defender.py` in the editor and click the **Run ▷** button in the
     top-right corner (or press `F5` / `Ctrl+F5`), **or**
   - Run it from the integrated terminal:
     ```powershell
     python defender.py
     ```

## Controls (defender.py)

| Key | Action |
|---|---|
| `LEFT` / `RIGHT` | Horizontal thrust (also sets facing direction) |
| `UP` / `DOWN` | Vertical thrust |
| `SPACE` | Fire laser |
| `B` | Smart bomb (destroys every enemy on screen) |
| `H` | Hyperspace (random teleport, brief invulnerability) |
| `ENTER` | Restart after Game Over |

## Other scripts

- `main.py`, `main2.py`, `main3.py`, `platformer.py` — other pygame
  experiments in this repo, run the same way (`python <file>.py`) once
  dependencies are installed.
