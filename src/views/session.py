from utils import TimeParser
import customtkinter as ctk
from typing import Any, Optional
import datetime
import time
from src.event import Event
from src.coordinator import EventCoordinator


parser = TimeParser()


class EventTimer(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame | ctk.CTkScrollableFrame,
        controller: ctk.CTkFrame,
        event: Event,
        **kwargs: Any,
    ):
        super().__init__(master)
        self.controller = controller
        self.event = event
        self.name_label = None
        self.timer_label = None
        self.status_label = None
        self.progress_bar = None

        self.show_counter()
        self.show_progress_bar()
        self.show_start_to_end()

    def show_counter(self) -> None:
        # event Name (Title)
        name = (
            self.event.summary if self.event and self.event.summary else "Unnamed Event"
        )
        self.name_label = ctk.CTkLabel(
            self,
            text=name,
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
        )
        self.name_label.pack(anchor="w", padx=(10, 10))

        # Countdown Timer (Digital Clock style)
        self.timer_label = ctk.CTkLabel(
            self,
            text="00 : 00 : 00",
            font=ctk.CTkFont("Segoe UI", 64, "bold"),
            text_color="#00ff88",
        )
        self.timer_label.pack(pady=(5, 0), fill="x", padx=(10, 10), expand=True)

        # Status Text
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont("Segoe UI", 11),
        )
        self.status_label.pack(pady=(2, 0))

        self.update_counter_content()

    def show_progress_bar(self) -> None:
        if self.progress_bar is None:
            self.progress_bar = ctk.CTkProgressBar(
                self,
                width=200,
                height=5,
                progress_color="#00ff88",
                border_color="#292929",
            )
            # stretch the progress bar to fill the width of the container
            self.progress_bar.pack(pady=(10, 0), anchor="w", padx=(10, 10), fill="x")
        if self.event and self.event.duration > 0:
            elapsed_ratio = self.event.elapsed_time / self.event.duration
            self.progress_bar.set(elapsed_ratio)
        else:
            self.progress_bar.set(1.0)

    def show_start_to_end(self) -> None:
        """
        Displays the start and end times of the event.
        """
        if self.event.start_time and self.event.end_time:
            end_str = self.event.end_time.strftime("%H:%M:%S")
            start_str = self.event.start_time.strftime("%H:%M:%S")
            start_end_text = f"{start_str} - {end_str}"
            start_end_label = ctk.CTkLabel(
                self,
                text=start_end_text,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color="#ffffff",
            )
            start_end_label.pack(pady=(2, 0), anchor="w", padx=(10, 10))

    def update_progress_bar(self) -> None:
        """
        Updates the progress bar based on the event's elapsed time and duration.
        If the event is running, it updates the elapsed time.
        """
        if self.event and self.event.is_running:
            progress_value = (
                self.event.elapsed_time / self.event.duration
                if self.event.duration > 0
                else 1.0
            )
            self.progress_bar.set(progress_value) if self.progress_bar else None

    def update_counter_content(self) -> None:
        elapsed = (
            time.strftime("%H : %M : %S", time.gmtime(self.event.elapsed_time))
            if self.event
            else "00 : 00 : 00"
        )
        duration = self.event.duration if self.event else None

        if self.event.elapsed_time >= self.event.duration:
            self.event.is_completed = True
            self.event.is_running = False
            timer_text = elapsed
            status_text = "✔ Completed"
            timer_color = "#019751"
        elif self.event and self.event.is_running:
            self.event.elapsed_time += 1
            elapsed = time.strftime(
                "%H : %M : %S", time.gmtime(self.event.elapsed_time)
            )
            timer_text = elapsed
            status_text = "▶ In Progress"
            timer_color = "#FFC107"
            # update progress bar
            self.update_progress_bar()
        elif elapsed == "00 : 00 : 00":
            elapsed = time.strftime("%H : %M : %S", time.gmtime(duration))
            timer_text = elapsed
            status_text = "⏳ Pending"
            timer_color = "#9E9E9E"

        else:
            timer_text = elapsed
            status_text = "⏸ Paused"
            timer_color = "#9E9E9E"

        # Update labels
        (
            self.timer_label.configure(text=timer_text, text_color=timer_color)
            if self.timer_label
            else None
        )
        self.status_label.configure(text=status_text) if self.status_label else None

        # Schedule next update
        self.after(1000, self.update_counter_content)


class EventCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        event: Event,
        index: int,
        fg_color="transparent",
        border_color="#292929",
        border_width=2,
    ):
        super().__init__(
            master,
            fg_color=fg_color,
            border_color=border_color,
            border_width=border_width,
        )
        self.index = index
        self.event = event
        self.render()

    def render(self):
        self.grid(row=self.index, column=0, padx=5, pady=(5, 0), sticky="ew")
        self.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            self,
            text=f"{self.event.summary}",
            font=ctk.CTkFont("Segoe UI", 12, "normal"),
        )
        label.grid(column=0, row=0, pady=(5, 0), padx=(10, 10), sticky="w")
        start_ = (
            self.event.start_time.strftime("%H:%M:%S")
            if self.event.start_time
            else "N/A"
        )
        end_ = (
            self.event.end_time.strftime("%H:%M:%S") if self.event.end_time else "N/A"
        )
        time_details = f"{start_} - {end_}"
        time_label = ctk.CTkLabel(
            self,
            text=time_details,
            font=ctk.CTkFont("Segoe UI", 10, "normal"),
            text_color="#747474",
        )
        time_label.grid(column=0, row=1, padx=(10, 10), pady=(5, 5), sticky="w")

        if self.event.is_completed:
            self.badge(self, "Completed").grid(
                column=1, row=0, padx=(10, 10), pady=(5, 0), sticky="e"
            )
        elif (
            isinstance(self.event.end_time, datetime.datetime)
            and self.event.end_time < datetime.datetime.now()
        ):
            self.badge(self, "Missed", "#DDFF00").grid(
                column=1, row=0, padx=(10, 10), pady=(5, 0), sticky="e"
            )
        else:
            self.badge(self, "Upcoming", "#9E9E9E").grid(
                column=1, row=0, padx=(10, 10), pady=(5, 0), sticky="e"
            )

    def badge(self, master, text: str, color: str = "#019751") -> ctk.CTkButton:
        text_color = "#ffffff" if color == "#019751" else "#000000"
        return ctk.CTkButton(
            master,
            text=text,
            text_color=text_color,
            text_color_disabled=text_color,
            width=30,
            height=10,
            corner_radius=25,
            font=ctk.CTkFont("Segoe UI", 8, "normal"),
            fg_color=color,
            state="disabled",
        )


class EventQueue(ctk.CTkScrollableFrame):
    def __init__(
        self,
        master: ctk.CTkFrame | ctk.CTkScrollableFrame,
        coordinator: EventCoordinator,
        **kwargs: Any,
    ):
        super().__init__(master, **kwargs)
        self.coordinator = coordinator
        self._last_completed: list[str] = []
        self._last_upcoming: list[str] = []
        self.grid_columnconfigure(0, weight=1)
        self.on_load()  # start periodic checking

    def render(self, completed: list[Event], upcoming: list[Event]) -> None:
        # clear existing children
        for widget in self.winfo_children():
            widget.destroy()

        events = completed + upcoming
        for i, event in enumerate(events):
            EventCard(self, event=event, index=i)

    def on_load(self):
        """Compare event lists with last known state and rerender only if changed"""
        completed, upcoming = (
            self.coordinator.completed_list(),
            self.coordinator.upcoming_list(),
        )
        # create a comparable signature (summary strings only)
        completed_keys = [e._id for e in completed]
        upcoming_keys = [e._id for e in upcoming]

        if (
            completed_keys != self._last_completed
            or upcoming_keys != self._last_upcoming
        ):
            self.render(list(completed), list(upcoming))
            self._last_completed = completed_keys
            self._last_upcoming = upcoming_keys

        self.after(1000, self.on_load)


class Spinner(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame | ctk.CTkScrollableFrame, **kwargs: Any):
        super().__init__(master, **kwargs)
        self.spinner = ctk.CTkLabel(
            self, text="Loading...", font=ctk.CTkFont("Segoe UI", 16, "bold")
        )
        self.spinner.pack(pady=(10, 0), padx=(10, 10))
        self.spinner.configure(text_color="#585858")
        self.after(1000, self.update_spinner)

    def update_spinner(self) -> None:
        self.spinner.configure(text="Please wait...")


class EventsView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        controller,
        coordinator=EventCoordinator,
        **kwargs: Any,
    ):
        super().__init__(master, **kwargs)
        self.coordinator = coordinator()
        self.controller = controller
        self.current_event = None

        self.grid_columnconfigure(index=0, weight=1)
        self.grid_rowconfigure(index=2, weight=1)

        self.timer_section = self.build_section("Current Event", scrollable=False)
        self.timer_section.columnconfigure(0, weight=1)
        self.timer_section.rowconfigure(1, weight=1)
        self.control_section = self.build_section(scrollable=False)
        self.control_section.columnconfigure(0, weight=1)
        self.control_section.rowconfigure(0, weight=1)
        self.queue_section = self.build_section("Event List", scrollable=False)
        self.queue_section.columnconfigure(0, weight=1)
        self.queue_section.rowconfigure(0, weight=0)

        self.spinner = Spinner(self.timer_section, height=200)
        self.spinner.grid(column=0, row=1, pady=(10, 0), padx=(10, 10), sticky="nsew")

        self.controls_container = ctk.CTkFrame(
            self.control_section, fg_color="transparent"
        )
        self.controls_container.grid(
            column=0, row=2, pady=(5, 10), padx=10, sticky="new"
        )
        self.controls_container.columnconfigure((0, 1, 2), weight=1)

        self.event_queue = EventQueue(self.queue_section, self.coordinator)
        self.event_queue.grid(column=0, row=1, pady=(5, 5), padx=10, sticky="nsew")

        self.build_controls()
        self.refresh()

    def build_section(
        self, title: Optional[str] = None, scrollable: bool = False
    ) -> ctk.CTkFrame | ctk.CTkScrollableFrame:
        """
        Builds a section with a title and a frame.
        Args:
            title (str): The title of the section.
            section (ctk.CTkFrame): The frame to display in the section.
        """
        if scrollable:
            section = ctk.CTkScrollableFrame(
                self, fg_color="transparent", border_color="#292929", border_width=2
            )
        else:
            section = ctk.CTkFrame(
                self, fg_color="transparent", border_color="#292929", border_width=2
            )
        if title:
            lbl_container = ctk.CTkFrame(section, fg_color="transparent")
            lbl_container.grid(row=0, column=0, sticky="nsew", padx=(10, 10))
            lbl_container.columnconfigure(0, weight=1)
            label = ctk.CTkLabel(
                lbl_container,
                text=title,
                font=ctk.CTkFont("Segoe UI", 12, "normal"),
                text_color="#ffffff",
            )
            label.grid(pady=(5, 0), padx=(10, 10), row=0, column=0, sticky="w")
        section.grid(padx=10, sticky="nsew", pady=10)
        section.grid_rowconfigure(1, weight=1)
        return section

    def build_controls(self):
        self.start_button = ctk.CTkButton(
            self.controls_container,
            text="Start",
            fg_color="#007f44",
            command=lambda *_: setattr(self.current_event, "is_running", True),
        )
        self.start_button.grid(column=0, row=0, padx=5, pady=5, sticky="ew")

        self.pause_button = ctk.CTkButton(
            self.controls_container,
            text="Pause",
            fg_color="#C4B101",
            text_color="#747474",
            command=lambda *_: setattr(self.current_event, "is_running", False),
        )
        self.pause_button.grid(column=1, row=0, padx=5, pady=5, sticky="ew")

        self.skip_button = ctk.CTkButton(
            self.controls_container,
            text="Skip",
            fg_color="#880000",
            text_color="#E6E6E6",
            command=self.skip_current_event,
        )
        self.skip_button.grid(column=2, row=0, padx=5, pady=5, sticky="ew")

    def refresh(self):
        next_event = self.coordinator.get_next_event()

        if next_event is self.current_event:
            return self.after(1000, self.refresh)

        if self.current_event:
            for widget in self.timer_section.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and any(
                    isinstance(child, ctk.CTkLabel)
                    and child.cget("text") == "Current Event"
                    for child in widget.winfo_children()
                ):
                    continue
                if isinstance(widget, EventTimer) and isinstance(widget.event, Event):
                    if next_event and widget.event._id == next_event._id:
                        widget.tkraise()
                        return self.after(1000, self.refresh)
                if (
                    isinstance(widget, ctk.CTkLabel)
                    and widget.cget("text") == "Loading..."
                ):
                    widget.configure(text="Please wait...")
                widget.grid_forget()

        if next_event is not None:
            self.load_event(next_event)
        self.after(1000, self.refresh)

    def load_event(self, event: Event):
        if not isinstance(event, Event):
            raise TypeError("Expected an instance of Event.")
        self.current_event = event
        timer = EventTimer(self.timer_section, self, event)
        timer.grid(column=0, row=1, padx=10, pady=5, sticky="new")
        timer.tkraise()

    def skip_current_event(self):
        new_event = self.coordinator.skip_current_event()
        if new_event and self.current_event and new_event._id != self.current_event._id:
            self.load_event(new_event)
