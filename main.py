import customtkinter as ctk
from PIL import ImageTk
from logging_config import *
import sys
from utils import ConfigManager
from utils import load_image
from src.app_services.managers import ServiceManager
from src.app_services.google_service import GoogleCalendarService
from src.views.session import EventsView
from src.coordinator import EventCoordinator
from src.app_services.service_loader import ServiceLoader


ServiceManager.register("google", "calendar", GoogleCalendarService)


class GazeTimeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GazeTime")
        self.geometry("400x700")
        self.resizable(False, False)
        image_data = load_image("app_icon.png", "icons")
        image = ImageTk.PhotoImage(image_data, size=(30, 30))
        self.iconphoto(True, image)  # type: ignore
        self.iconbitmap()
        self.first_launch = ConfigManager.get("first_time", default=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if self.first_launch:
            ConfigManager.save_config(data={"first_time": False})
        self.launch_main_ui()

    def launch_main_ui(self):
        self.deiconify()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True)
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self.view_stack = []  # For navigation history
        self.current_view = None
        self.service_manager = ServiceManager()
        self.coordinator = EventCoordinator()
        self.service_loader = ServiceLoader()
        self.service_loader.set_coordinator(self.coordinator)
        self.show_content(EventsView)

    def show_content(self, ViewClass, *args, **kwargs):
        if self.current_view:
            # Save current view to stack
            self.view_stack.append(self.current_view)

        self.current_view = ViewClass(self.content, self, *args, **kwargs)
        self.current_view.grid(column=0, row=0, sticky="nsew")
        self.current_view.tkraise()

    def go_back(self):
        if self.view_stack:
            # Destroy current view
            if self.current_view:
                self.current_view.grid_forget()
                self.current_view.destroy()

            # Restore last view
            self.current_view = self.view_stack.pop()
            if hasattr(self.current_view, "refresh"):
                self.current_view.refresh()
            self.current_view.tkraise()

    def on_close(self):
        self.service_loader.shutdown()
        self.destroy()
        sys.exit(0)


if __name__ == "__main__":
    ctk.set_default_color_theme("dark-blue")
    mode = ConfigManager.get("theme", default="System")
    ctk.set_appearance_mode(mode)
    app = GazeTimeApp()
    app.mainloop()
