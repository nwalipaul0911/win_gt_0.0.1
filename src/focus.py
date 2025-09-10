import keyboard
import threading
from utils import AppInspector, ConfigManager
import time
from typing import Any, Optional, Dict


class KeystrokeBlocker:
    """
    A class that blocks all keystrokes globally on the system when activated.
    Uses the `keyboard` library to intercept key events and a background thread
    to manage the hook listener.
    """

    def __init__(self) -> None:
        """
        Initializes the keystroke blocker and starts a background thread to listen
        for keyboard events. By default, key blocking is disabled.
        """
        self.blocking = False  # Indicates whether keystrokes should be blocked
        self.listener = threading.Thread(target=self._listener, daemon=True)
        self.listener.start()  # Start the key listener thread

    def _block_keys(self, event: Optional[keyboard.KeyboardEvent] = None) -> bool:
        """
        Internal method called for every key event. Determines whether the key should be blocked.

        Args:
            event (keyboard.KeyboardEvent): The keyboard event being handled.

        Returns:
            bool: False if blocking is enabled (suppress event), True otherwise.
        """
        return not self.blocking  # If blocking is True, return False to suppress key

    def _listener(self) -> None:
        """
        Background thread function to set up the keyboard hook.
        """
        keyboard.hook(self._block_keys, suppress=True)
        keyboard.wait()  # Keeps the thread alive and actively listening

    def block(self) -> None:
        """
        Enables global keystroke blocking.
        """
        self.blocking = True

    def unblock(self) -> None:
        """
        Disables global keystroke blocking.
        """
        self.blocking = False


class Focus:
    _instance = None

    def __new__(cls) -> Any:
        if cls._instance is None:
            cls._instance = super(Focus, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return  # Avoid reinitialization

        self._initialized = True
        self.keyblocker = KeystrokeBlocker()
        self.focus_apps: list[str] = []
        self.enabled = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.default: Dict[str, Any] = {"apps": [], "keyblocker": False}

        self.load()

    def load(self) -> None:
        """Load configuration from disk."""
        config = ConfigManager.get("focus", self.default)
        self.focus_apps = config.get("apps", [])

    def save(self) -> None:
        """Save current config."""
        ConfigManager.save_config({"focus": {"apps": self.focus_apps}})

    def update_focus_apps(self, apps: list[str], overwrite: bool = False) -> None:
        """Update the list of apps to focus on."""
        if overwrite:
            self.focus_apps = apps
        else:
            for app in apps:
                if app not in self.focus_apps:
                    self.focus_apps.append(app)
        self.save()

    def turn_on(self) -> None:
        """Enable keystroke blocking when non-focus apps are active."""
        if self.enabled:
            return

        self.enabled = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._watcher, daemon=True)
        self._thread.start()
        self.save()

    def turn_off(self) -> None:
        """Disable focus checking and unblock keys."""
        self.enabled = False
        self._stop_event.set()
        self.keyblocker.unblock()
        self.save()

    def _watcher(self) -> None:
        """Background thread to monitor active window and block keys."""
        while not self._stop_event.is_set():
            active = AppInspector.get_active_process_name()
            if active:
                if active.lower() not in [app.lower() for app in self.focus_apps]:
                    self.keyblocker.block()
                else:
                    self.keyblocker.unblock()
            time.sleep(1)
