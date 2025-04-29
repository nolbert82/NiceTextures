import sys
import threading
import os
import configparser
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSystemTrayIcon, QMenu, QLabel # Added QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QRect # Added QRect
from PyQt6.QtGui import QPainter, QPixmap, QColor, QGuiApplication, QIcon
from pynput import keyboard

# Signal bridge to communicate from pynput thread to PyQt thread
class SignalBridge(QObject):
    toggleSignal = pyqtSignal()
    increaseOpacitySignal = pyqtSignal()
    decreaseOpacitySignal = pyqtSignal()
    nextTextureSignal = pyqtSignal()
    previousTextureSignal = pyqtSignal()

signal_bridge = SignalBridge()

# --- Configuration Loading ---
DEFAULT_HOTKEYS = {
    'toggle': '<ctrl>+<alt>+t',
    'increase_opacity': '<ctrl>+<alt>+<up>',
    'decrease_opacity': '<ctrl>+<alt>+<down>',
    'next_texture': '<ctrl>+<alt>+<right>',
    'previous_texture': '<ctrl>+<alt>+<left>',
}
DEFAULT_STARTUP = {
    'opacity': 0.5,
    'texture': None, # None means load the first available
    'enabled': False # Default to not visible on startup
}

# --- Resource Handling (for PyInstaller) ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_config():
    CONFIG_FILE = resource_path('config.ini')
    config = configparser.ConfigParser()
    read_files = config.read(CONFIG_FILE)

    hotkeys = DEFAULT_HOTKEYS.copy()
    startup = DEFAULT_STARTUP.copy()

    if read_files: # If config file was read successfully
        if 'Hotkeys' in config:
            hotkeys['toggle'] = config['Hotkeys'].get('ToggleOverlay', DEFAULT_HOTKEYS['toggle'])
            hotkeys['increase_opacity'] = config['Hotkeys'].get('IncreaseOpacity', DEFAULT_HOTKEYS['increase_opacity'])
            hotkeys['decrease_opacity'] = config['Hotkeys'].get('DecreaseOpacity', DEFAULT_HOTKEYS['decrease_opacity'])
            hotkeys['next_texture'] = config['Hotkeys'].get('NextTexture', DEFAULT_HOTKEYS['next_texture'])
            hotkeys['previous_texture'] = config['Hotkeys'].get('PreviousTexture', DEFAULT_HOTKEYS['previous_texture'])
        if 'Startup' in config:
            try:
                startup['opacity'] = max(0.1, min(1.0, config['Startup'].getfloat('InitialOpacity', DEFAULT_STARTUP['opacity'])))
            except ValueError:
                print(f"Warning: Invalid InitialOpacity value in {CONFIG_FILE}. Using default.")
                startup['opacity'] = DEFAULT_STARTUP['opacity']
            startup['texture'] = config['Startup'].get('InitialTexture', DEFAULT_STARTUP['texture']) or None # Ensure empty string becomes None
            try:
                startup['enabled'] = config['Startup'].getboolean('OverlayEnabled', DEFAULT_STARTUP['enabled'])
            except ValueError:
                print(f"Warning: Invalid OverlayEnabled value in {CONFIG_FILE}. Using default.")
                startup['enabled'] = DEFAULT_STARTUP['enabled']
    else:
        print(f"Warning: {CONFIG_FILE} not found or could not be read. Using default hotkeys and startup settings.")

    print(f"Loaded Hotkeys: {hotkeys}")
    print(f"Loaded Startup Settings: {startup}")
    return hotkeys, startup

# --- Hotkey Setup ---

def setup_hotkeys(config_hotkeys):
    # Define actions using the signal bridge
    actions = {
        config_hotkeys['toggle']: signal_bridge.toggleSignal.emit,
        config_hotkeys['increase_opacity']: signal_bridge.increaseOpacitySignal.emit,
        config_hotkeys['decrease_opacity']: signal_bridge.decreaseOpacitySignal.emit,
        config_hotkeys['next_texture']: signal_bridge.nextTextureSignal.emit,
        config_hotkeys['previous_texture']: signal_bridge.previousTextureSignal.emit,
    }

    # Start the global hotkey listener
    # GlobalHotKeys runs its own daemon thread
    hotkey_listener = keyboard.GlobalHotKeys(actions)
    hotkey_listener.start()
    print("Hotkey listener started.")
    # Return the listener object so it doesn't get garbage collected
    # and its thread stops. The main thread needs to keep a reference.
    return hotkey_listener

class OverlayWidget(QWidget):
    def __init__(self, parent=None, initial_opacity=0.5, initial_texture=None):
        super().__init__(parent)
        self.texture = None
        self.opacity = initial_opacity
        self.textures_dir = resource_path('textures') # Directory for textures
        self.texture_files = []
        self.current_texture_index = -1
        self.find_textures()

        if initial_texture:
            initial_texture_path = os.path.join(self.textures_dir, initial_texture)
            self.load_specific_texture(initial_texture_path)
        elif self.texture_files: # Only load next if textures were found
            self.load_next_texture() # Load the first found texture
        else:
            print("Warning: No initial texture specified and no textures found in directory.")
            # Optionally load a default built-in texture or show nothing

    def find_textures(self):
        self.texture_files = []
        if not os.path.isdir(self.textures_dir):
            print(f"Warning: Textures directory '{self.textures_dir}' not found or is not a directory.")
            # We don't create it here anymore as it should be bundled by PyInstaller
            return

        try:
            for f in os.listdir(self.textures_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    self.texture_files.append(os.path.join(self.textures_dir, f))
            self.texture_files.sort()
        except Exception as e:
            print(f"Error reading textures directory: {e}")

        self.current_texture_index = -1 # Reset index before loading next
        print(f"Found textures: {self.texture_files}")

    def load_specific_texture(self, texture_path):
        # Use os.path.normpath for consistent comparisons
        norm_texture_path = os.path.normpath(texture_path)
        norm_file_list = [os.path.normpath(f) for f in self.texture_files]

        if norm_texture_path in norm_file_list:
            self.current_texture_index = norm_file_list.index(norm_texture_path)
            print(f"Loading specific texture: {texture_path}")
            self.load_texture(texture_path)
        else:
            print(f"Warning: Initial texture '{texture_path}' not found in available textures {self.texture_files}. Loading first available.")
            if self.texture_files: # Check if there are any textures
                self.load_next_texture()
            else:
                # Handle case where specified texture not found AND no other textures exist
                self.texture = None # Ensure no texture is loaded
                self.update()

    def load_next_texture(self):
        if not self.texture_files:
            print("No textures found or loaded.")
            return

        self.current_texture_index = (self.current_texture_index + 1) % len(self.texture_files)
        texture_path = self.texture_files[self.current_texture_index]
        print(f"Loading next texture: {texture_path}")
        self.load_texture(texture_path)

    def load_previous_texture(self):
        if not self.texture_files:
            print("No textures found or loaded.")
            return

        # Correct modulo arithmetic for negative numbers in Python
        self.current_texture_index = (self.current_texture_index - 1 + len(self.texture_files)) % len(self.texture_files)
        texture_path = self.texture_files[self.current_texture_index]
        print(f"Loading previous texture: {texture_path}")
        self.load_texture(texture_path)

    def load_texture(self, path):
        # Path should already be correct (either relative or absolute from resource_path)
        self.texture = QPixmap(path)
        if self.texture.isNull():
            print(f"Warning: Could not load texture from {path}")
            # Create a fallback texture (e.g., simple noise or solid color)
            self.texture = QPixmap(100, 100)
            # Use current opacity for fallback fill
            self.texture.fill(QColor(128, 128, 128, int(self.opacity * 128))) # Gray fallback
        self.update() # Trigger repaint

    def set_opacity(self, opacity):
        self.opacity = max(0.0, min(1.0, opacity)) # Allow 0.0 opacity
        print(f"Opacity set to: {self.opacity:.2f}")
        self.update() # Trigger repaint

    def paintEvent(self, event):
        if not self.texture or self.opacity == 0.0:
            return

        painter = QPainter(self)
        painter.setOpacity(self.opacity)

        # Tile the texture across the widget
        widget_rect = self.rect()
        texture_size = self.texture.size()

        if texture_size.width() > 0 and texture_size.height() > 0:
             for x in range(0, widget_rect.width(), texture_size.width()):
                for y in range(0, widget_rect.height(), texture_size.height()):
                    painter.drawPixmap(x, y, self.texture)

        painter.end()

# --- OSD Popup --- Indicator like volume control
class OsdPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool | # Avoid showing in taskbar
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput # Click-through
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180); color: white; border-radius: 5px; padding: 10px; font-size: 16px;")

        self.layout = QVBoxLayout(self)
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(1500) # Hide after 1.5 seconds
        self.hide_timer.timeout.connect(self.hide)

    def show_message(self, message):
        self.label.setText(message)
        self.adjustSize() # Adjust size based on content
        # Center it on the primary screen
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        # popup_geometry = self.frameGeometry() # Not needed for centering
        self.move(screen_geometry.center() - self.rect().center())

        self.show()
        self.hide_timer.start()

class MainWindow(QMainWindow):
    def __init__(self, startup_config):
        super().__init__()
        self.overlay_visible = startup_config.get('enabled', True) # Get initial state from config
        self.startup_config = startup_config
        self.initUI()

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool | # Avoid showing in taskbar/alt-tab
            Qt.WindowType.WindowTransparentForInput # Make window click-through
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background:transparent;")

        # Determine total screen geometry
        screens = QGuiApplication.screens()
        total_geometry = QGuiApplication.primaryScreen().virtualGeometry()
        # TODO: This might need refinement for multi-monitor setups with different positions/scales

        self.setGeometry(total_geometry)

        self.central_widget = OverlayWidget(self, initial_opacity=self.startup_config['opacity'], initial_texture=self.startup_config['texture'])
        self.setCentralWidget(self.central_widget)

        self.setWindowTitle('NiceTextures Overlay')
        # Only show initially if configured to be visible
        if self.overlay_visible:
            # Use show() instead of showFullScreen() to respect geometry
            self.show()
        # else: it starts hidden
        # Create the OSD popup
        self.osd_popup = OsdPopup()

    def toggle_visibility(self):
        self.overlay_visible = not self.overlay_visible
        if self.overlay_visible:
            self.show()
            print("Overlay: ON")
            self.osd_popup.show_message("Overlay: ON") # Also show OSD
        else:
            self.hide()
            print("Overlay: OFF")
            self.osd_popup.show_message("Overlay: OFF") # Also show OSD

    def change_opacity(self, delta=0.05):
        print(f"Changing opacity by: {delta}")
        # Use round to avoid floating point issues when comparing/stepping
        current_opacity = round(self.central_widget.opacity, 1)
        new_opacity = current_opacity + delta

        # Clamp opacity between 0.0 and 1.0 (Allowing 0% opacity)
        new_opacity_clamped = max(0.0, min(1.0, round(new_opacity, 1)))

        # Prevent changing if already at min/max in the direction of delta
        if (delta > 0 and current_opacity >= 1.0) or (delta < 0 and current_opacity <= 0.0):
             print("Opacity already at limit.")
             # Optionally show OSD with current value anyway?
             self.osd_popup.show_message(f"Opacity: {int(current_opacity * 100)}%")
             return

        self.central_widget.set_opacity(new_opacity_clamped)
        # Show OSD
        self.osd_popup.show_message(f"Opacity: {int(new_opacity_clamped * 100)}%")

    def next_texture(self):
        if not self.central_widget.texture_files:
            self.osd_popup.show_message("No Textures Found")
            return
        print("Next texture hotkey triggered")
        self.central_widget.load_next_texture()
        # Show OSD (only if texture actually loaded/changed)
        if self.central_widget.texture:
             self.osd_popup.show_message(f"Texture: {os.path.basename(self.central_widget.texture_files[self.central_widget.current_texture_index])}")
        else:
             self.osd_popup.show_message("Texture Load Failed")


    def previous_texture(self):
        if not self.central_widget.texture_files:
            self.osd_popup.show_message("No Textures Found")
            return
        print("Previous texture hotkey triggered")
        self.central_widget.load_previous_texture()
        # Show OSD (only if texture actually loaded/changed)
        if self.central_widget.texture:
             self.osd_popup.show_message(f"Texture: {os.path.basename(self.central_widget.texture_files[self.central_widget.current_texture_index])}")
        else:
             self.osd_popup.show_message("Texture Load Failed")


    # Override close event if needed, e.g., to hide instead of exit
    # def closeEvent(self, event):
    #     self.hide()
    #     event.ignore()

def main():
    app = QApplication(sys.argv)

    # Load configuration
    config_hotkeys, startup_config = load_config()

    # Required for WA_TranslucentBackground to work reliably on some platforms
    app.setAttribute(Qt.ApplicationAttribute.AA_SynthesizeMouseForUnhandledTouchEvents, False)
    app.setAttribute(Qt.ApplicationAttribute.AA_SynthesizeTouchForUnhandledMouseEvents, False)

    # Prevent app exit when overlay window is hidden, rely on tray icon quit
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(startup_config)

    # Connect signals *after* window is created
    signal_bridge.toggleSignal.connect(window.toggle_visibility)
    signal_bridge.increaseOpacitySignal.connect(lambda: window.change_opacity(0.05))
    signal_bridge.decreaseOpacitySignal.connect(lambda: window.change_opacity(-0.05))
    signal_bridge.nextTextureSignal.connect(window.next_texture)
    signal_bridge.previousTextureSignal.connect(window.previous_texture)

    # Start hotkey listener and keep a reference
    hotkey_listener_ref = setup_hotkeys(config_hotkeys)

    # Setup System Tray Icon
    icon_path = resource_path("icon.png")
    if not os.path.exists(icon_path):
        print(f"Warning: {icon_path} not found. Tray icon may be default/invisible.")
        icon = QIcon() # Creates a null icon
    else:
        icon = QIcon(icon_path)

    tray_icon = QSystemTrayIcon(icon, parent=app)
    tray_icon.setToolTip("NiceTextures Overlay")

    menu = QMenu()
    toggle_action = menu.addAction(f"Toggle Overlay ({config_hotkeys['toggle']})")
    toggle_action.triggered.connect(window.toggle_visibility)
    increase_opacity_action = menu.addAction(f"Increase Opacity ({config_hotkeys['increase_opacity']})")
    increase_opacity_action.triggered.connect(lambda: window.change_opacity(0.05))
    decrease_opacity_action = menu.addAction(f"Decrease Opacity ({config_hotkeys['decrease_opacity']})")
    decrease_opacity_action.triggered.connect(lambda: window.change_opacity(-0.05))
    next_texture_action = menu.addAction(f"Next Texture ({config_hotkeys['next_texture']})")
    next_texture_action.triggered.connect(window.next_texture)
    prev_texture_action = menu.addAction(f"Previous Texture ({config_hotkeys['previous_texture']})")
    prev_texture_action.triggered.connect(window.previous_texture)
    # texture_action.triggered.connect(window.next_texture) # Removed duplicate connection
    menu.addSeparator()
    quit_action = menu.addAction("Quit")
    quit_action.triggered.connect(app.quit) # Use app.quit to properly exit
    tray_icon.setContextMenu(menu)
    tray_icon.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main() 