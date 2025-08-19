import os
import win32gui
import win32process
import psutil
from PIL import Image, ImageFile
import re
import json
import customtkinter as ctk
from functools import lru_cache
import datetime
from typing import Optional, Any, Dict, Set

# Base directory of the current file (used for loading assets)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Default config file path
CONFIG = "config.json"

class AppInspector:
    @staticmethod
    def is_window_visible_on_taskbar(hwnd: int) -> bool:
        """
        Checks if a window is visible and has a title (i.e., likely a user-facing application).

        Args:
            hwnd (int): Handle to the window.

        Returns:
            bool: True if the window is visible and has a title, False otherwise.
        """
        if not win32gui.IsWindowVisible(hwnd) or not win32gui.GetWindowText(hwnd):
            return False
        return True

    @staticmethod
    def get_running_apps() -> list[str]:
        """
        Retrieves a list of unique process names for all visible user-facing applications.

        Returns:
            list[str]: Sorted list of unique process names.
        """
        names: Set[str] = set()

        def callback(hwnd: int, _: Optional[int]) -> None:
            if AppInspector.is_window_visible_on_taskbar(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc_name = psutil.Process(pid).name().lower()
                    window_title = proc_name.split(".")[0].lower()
                    if proc_name == "applicationframehost.exe":
                        window_title = win32gui.GetWindowText(hwnd).lower()
                    names.add(window_title)
                except psutil.NoSuchProcess:
                    pass  # Process might have exited during enumeration
            return None
        win32gui.EnumWindows(callback, None)
        return sorted(names)

    @staticmethod
    def get_active_process_name() -> Optional[str]:
        """
        Retrieves the name of the process currently in the foreground window.
        Handles UWP apps like WhatsApp that run under ApplicationFrameHost.exe.

        Returns:
            str or None: The name of the active process (e.g., 'chrome.exe')
        """
        hwnd = win32gui.GetForegroundWindow()

        if hwnd == 0:
            return None  # No active window

        # Get the process ID for the active window
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        try:
            proc_name : str = psutil.Process(pid).name().lower()

            # Handle UWP container
            if proc_name == "applicationframehost.exe":
                window_title : str = win32gui.GetWindowText(hwnd).lower()
                return window_title.split(".")[0]
            return proc_name.split(".")[0]
        except psutil.NoSuchProcess:
            return None



def load_image(filename: str, dir: str) -> Image.Image:
    """
    Loads an image from the assets directory.

    Args:
        filename (str): The name of the image file.
        dir (str): Subdirectory under 'assets' where the file is located.

    Returns:
        PIL.Image.Image: Loaded image object.
    """
    image_path = os.path.join(BASE_DIR, "assets", dir, filename)
    return Image.open(image_path, "r")




class TimeParser:
    """
    Handles conversion between human-readable time strings and seconds.
    """

    def dehumanize(self, text: str) -> Optional[int]:
        """
        Converts human-readable time (e.g., "1h 30m") into total seconds.

        Args:
            text (str): Time string to parse.

        Returns:
            int | None: Total seconds represented by the string, or None on failure.
        """
        try:
            @lru_cache
            def wrapper(text: str) -> int: 
                text = str(text)
                pattern = r"""
                    (?:(\d+)\s*h)?\s*
                    (?:(\d+)\s*m)?\s*
                    (?:(\d+)\s*s)?\s*
                    (?:(\d+)\s*)?\s*
                """
                match = re.fullmatch(pattern, text.strip(), re.IGNORECASE | re.VERBOSE)
                if not match:
                    raise ValueError(f"Invalid format: '{text}'")

                hours   = int(match.group(1)) if match.group(1) else 0
                minutes = int(match.group(2)) if match.group(2) else 0
                second1 = int(match.group(3)) if match.group(3) else 0
                second2 = int(match.group(4)) if match.group(4) else 0

                return hours * 3600 + minutes * 60 + second1 + second2
            return wrapper(text)
        except ValueError:
            return None
        except TypeError:
            return None

    def humanize(self, text: Optional[str | int]) -> Optional[str]:
        """
        Converts seconds into a human-readable format (e.g., "1h30m").

        Args:
            text (int or str): Number of seconds.

        Returns:
            str: Human-readable string.
        """
        try:
            @lru_cache
            def wrapper(text: str| int) -> str:
                seconds = int(text)
                parts = ""
                hours, seconds = divmod(seconds, 3600)
                minutes, seconds = divmod(seconds, 60)

                if hours:
                    parts += f"{hours}h"
                if minutes:
                    parts += f"{minutes}m"
                if seconds or not parts:
                    parts += f"{seconds}s"

                return parts
            return wrapper(text)
        except ValueError:
            return None
        except TypeError:
            return None
        
class InputValidator:
    """
    Provides static methods to validate name and time inputs in GUI fields.
    """

    @staticmethod
    def validate_name(name: ctk.StringVar, entry: ctk.CTkEntry) -> bool:
        """
        Validates that the name is not empty.

        Args:
            name (tk.StringVar): Name variable.
            entry: UI widget to update styling.

        Returns:
            bool: True if valid, False otherwise.
        """
        if len(name.get()) < 1:
            entry.configure(border_color="red")
            return False
        entry.configure(border_color="#292929")
        return True

    @staticmethod
    def validate_time(var: ctk.StringVar, entry: ctk.CTkEntry, *args: Any) -> bool:
        """
        This function validates a human readable time string for correct conversion to seconds

        Args:
            var (tk.StringVar): Time string variable.
            entry: UI widget to style.

        Returns:
            bool: True if valid, False otherwise.
        """
        parser = TimeParser()
        is_valid = parser.dehumanize(var.get())
        entry.configure(border_color="#292929" if is_valid else "red")
        return is_valid is not None
    
    @staticmethod
    def validate_schedule(var: ctk.StringVar, entry: ctk.CTkEntry, *args: Any) -> bool:
        """
        Validates that `var` a scheduled time is valid and not in the past.

        Args:
            var (tk.StringVar): Time string variable.
            entry: UI widget to style.

        Returns:
            bool: True if valid, False otherwise.
        """
        time_str = var.get().strip()

        matches = re.match(r"\d{2}(:)\d{2}(?!.)", time_str)
        is_valid = matches != None
        try:
            if is_valid:
                schedule_time = datetime.datetime.strptime(time_str, "%H:%M").time()
                now = datetime.datetime.now()
                schedule_dt = datetime.datetime.combine(now.date(), schedule_time)
                is_valid = schedule_dt > now
            entry.configure(border_color="#292929" if is_valid else "red")
            return is_valid
        except Exception as e:
            entry.configure(border_color="red")
            return False
        


class ConfigManager:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get(config: str, default: Any="default") -> Any:
        if os.path.exists(CONFIG):
            with open(CONFIG, "r") as f:
                try:
                    config = json.load(f).get(config, default)
                    return config
                except json.JSONDecodeError:
                    return default
        return default
    
    @staticmethod
    def load_config()-> (Dict[str, Any] | Any):
        if not os.path.exists(CONFIG):
            return {}
        with open(CONFIG, "r") as f:
            return json.load(f)

    @staticmethod
    def save_config(data : Dict[str, Any]) -> None:
        config = ConfigManager.load_config()  # Load existing config
        config.update(data)                   # Merge new values
        with open(CONFIG, "w") as f:
            json.dump(config, f, indent=4)


