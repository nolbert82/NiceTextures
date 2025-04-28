# NiceTextures

A simple Windows application to overlay a texture (like paper, noise, etc.) on your screen to potentially ease eye strain while reading or working.

## Features

*   **Screen Overlay:** Displays a semi-transparent texture over your entire screen(s).
*   **Configurable Hotkeys:** Control the overlay using global hotkeys.
    *   Toggle overlay visibility.
    *   Increase/Decrease texture opacity.
    *   Cycle through available textures (next/previous).
*   **Texture Support:** Loads `.png`, `.jpg`, `.jpeg`, `.bmp`, `.gif` files from a `textures` directory.
*   **Customizable Startup:** Configure initial opacity, initial texture, and initial visibility via `config.ini`.
*   **System Tray Icon:** Provides easy access to toggle, change opacity/texture, and quit the application.
*   **Click-Through:** The overlay doesn't interfere with mouse clicks on underlying windows.
*   **OSD Indicator:** Shows a brief popup indicating opacity level or current texture when changed via hotkeys.
*   **Bundled Executable:** Can be built into a single `.exe` file for portability.

## Configuration (`config.ini`)

The application uses a `config.ini` file (created automatically if missing, using defaults) for customization:

*   **`[Hotkeys]` Section:**
    *   `ToggleOverlay`: Hotkey to show/hide the overlay.
    *   `IncreaseOpacity`: Hotkey to make the texture more opaque.
    *   `DecreaseOpacity`: Hotkey to make the texture more transparent.
    *   `NextTexture`: Hotkey to switch to the next texture file.
    *   `PreviousTexture`: Hotkey to switch to the previous texture file.
    *   *(Uses `pynput` key format, e.g., `<ctrl>+<alt>+t`, `<ctrl_r>+<f1>`, `<up>`)*
*   **`[Startup]` Section:**
    *   `InitialOpacity`: Opacity level on launch (e.g., `0.5` for 50%).
    *   `InitialTexture`: Filename (e.g., `paper.png`) within the `textures` folder to load first. Leave blank to load the first one found.
    *   `OverlayEnabled`: Set to `true` or `false` to control if the overlay is visible immediately on launch.

## Default Hotkeys

*   **Toggle Overlay:** `Ctrl_R + Alt + T` (Right Ctrl)
*   **Increase Opacity:** `Ctrl + Alt + UpArrow`
*   **Decrease Opacity:** `Ctrl + Alt + DownArrow`
*   **Next Texture:** `Ctrl + Alt + RightArrow`
*   **Previous Texture:** `Ctrl + Alt + LeftArrow`

*(These can be changed in `config.ini`)*

## How to Use

1.  **Place Textures:** Put your desired `.png`, `.jpg`, etc., texture files into the `textures` folder.
2.  **Configure (Optional):** Edit `config.ini` to change hotkeys or startup behavior.
3.  **Run:**
    *   **Executable:** Double-click `NiceTextures.exe` (found in the `dist` folder after building).
    *   **From Source:** Run `python main.py` in your terminal.
4.  **Control:** Use the configured hotkeys or right-click the system tray icon.

## Building from Source

1.  Install dependencies: `pip install -r requirements.txt`
2.  Install PyInstaller: `pip install pyinstaller`
3.  Run the build script: `build.bat`
    *   The executable (`NiceTextures.exe`) will be created in the `dist` folder.

## Dependencies

*   PyQt6
*   pynput 