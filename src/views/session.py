from plyer import notification
from utils import TimeParser
import datetime
import customtkinter as ctk
import  uuid
from logging_config import session_logger
from typing import Any, Optional, List, Dict, Tuple
from dataclasses import dataclass, field
import heapq
import time
import threading
from src.app_services.managers import ServiceManager

parser = TimeParser()

@dataclass
class EventData:
    """
    Represents the data for an event.
    It includes the event's ID, summary, start and end times, duration, source.
    """

    
@dataclass
class Event(EventData):
    """
    Represents a single Event of time within a session.
    It tracks time, manages notifications, and supports pausing/resuming.
    """
    _id: str = str(uuid.uuid4())
    summary: str = "Unnamed Event"
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    duration: float = 0.0
    source: Optional[str] = None
    elapsed: int = 0
    is_running: bool = False
    is_scheduled: bool = False
    is_completed: bool = False
    focus: bool = False
    def __post_init__(self)-> None:
        if isinstance(self.start_time, datetime.datetime) and isinstance(self.end_time, datetime.datetime):
            self.duration = abs(self.end_time - self.start_time).total_seconds()
        if self.start_time is not None:
            self.is_scheduled = True

    def get_time_before(self) -> Optional[int]:
        if self.start_time is not None:
            return int((self.start_time - datetime.datetime.now()).total_seconds())
        return None
    
    def is_due(self) -> bool:
        """
        Checks if the event is due to start.
        Args:
            event (Event): The event to check.
        Returns:
            bool: True if the event is due, False otherwise.
        """
        if not self.start_time:
            return False
        return self.start_time <= datetime.datetime.now()
    
    def set_duration(self, duration: int) -> None:
        """
        Sets the duration of the event.
        Args:
            duration (int): Duration in seconds.
        """
        if duration < 0:
            session_logger.error("Duration cannot be negative.")
            raise ValueError("Duration cannot be negative.")
        if not self.is_scheduled:
            self.duration = duration
        else:  # If the event is scheduled, we adjust the end time accordingly
            if self.source is not None and self.source != "user":
                session_logger.error(f"Setting duration for scheduled event from {self.source} is not allowed.")
                return
            self.end_time = self.start_time + datetime.timedelta(seconds=duration) if self.start_time else None
            self.duration = duration

    def set_focus(self, focus: bool) -> None:
        """
        Sets the focus state of the event.
        Args:
            focus (bool): True if the event is focused, False otherwise.
        """
        self.focus = focus

    @property
    def elapsed_time(self) -> int:
        """
        Returns the elapsed time in seconds since the event started.
        If the event is not running, it returns the elapsed time stored.
        """
        return self.elapsed    
    
    @elapsed_time.setter
    def elapsed_time(self, value: int) -> None:
        """
        Sets the elapsed time for the event.
        Args:
            value (int): Elapsed time in seconds.
        """
        if value < 0:
            session_logger.error("Elapsed time cannot be negative.")
            raise ValueError("Elapsed time cannot be negative.")
        self.elapsed = value

    def notify(self) -> None:
        """
        Sends a desktop notification for the event.
        """
        if self.summary:
            notification.notify(
                title="Event Notification",
                message=self.summary,
                timeout=10,
            )
            session_logger.info(f"Notification sent for event: {self.summary}")
        else:
            session_logger.warning("No summary provided for notification.")


@dataclass(order=True)
class PrioritizedEvent:
    priority: float
    event: Event = field(compare=False)

class Coordinator:
    _instance = None
    _lock = threading.Lock()
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance


class EventCoordinator(Coordinator):
    _instances: Dict[str, Event] = {}
    _loader_started = False
    def __init__(self, **kwargs: Any):
        self._event_heap: List[PrioritizedEvent] = []
        self.current_event: Optional[Event] = None
        self.run_loader()


    def run_loader(self):
        # Prevent spawning multiple loader threads
        if not self.__class__._loader_started:
            self.__class__._loader_started = True
            threading.Thread(target=self.load_events, daemon=True).start()

    def load_events(self):
        services = ServiceManager().get_all_services("calendar")
        if not services:
            session_logger.warning("No calendar services available.")
            return
        while True:
            for platform, service_cls in services.items():
                service_instance = service_cls()
                if not service_instance:
                    session_logger.warning(f"Service {platform} is not authenticated.")
                    continue
                try:
                    events = service_instance.get_service_data()
                    
                    for event_data in events:
                        event = Event(
                            _id=event_data.get("id", str(uuid.uuid4())),
                            summary=event_data.get("summary", "Unnamed Event"),
                            start_time=event_data.get("start"),
                            end_time=event_data.get("end"),
                            source=platform
                        )
                        self.add_event(event)
                except Exception as e:
                    session_logger.error(f"Error loading events from {platform} service: {e}")
                    continue
            time.sleep(60)
        
        
    def add_event(self, event: Event) -> None:
        self._instances[event._id] = event
        self._rebuild_heap(list(self._instances.values()))

    def remove_event(self, event: Event) -> None:
        del self._instances[event._id]
        self._rebuild_heap(list(self._instances.values()))

    def _rebuild_heap(self, events: List[Event]) -> None:
        """Recalculate all priorities and rebuild the heap."""
        self._event_heap = [
            PrioritizedEvent(self.event_priority(e), e)
            for e in events if not e.is_completed or not e.is_due()
        ]
        heapq.heapify(self._event_heap)

    def update_priorities(self) -> None:
        """Call periodically to refresh queue based on real-time state."""
        self._rebuild_heap(list(self._instances.values()))

    def event_priority(self, event: Event) -> float:
        """
        Priority:
        - Scheduled events: higher priority the closer to start time.
        - Unscheduled events: run now, shorter durations first.
        Lower return value = higher priority.
        """
        now = datetime.datetime.now()

        # Scheduled events
        if event.start_time:
            seconds_until_start = (event.start_time - now).total_seconds()
            if seconds_until_start < 0:
                # If the event is in the past, it has no priority
                return float('inf')
            return seconds_until_start
        return event.duration - event.elapsed_time
    
    def peek_next_event(self) -> Optional[Event]:
        return self._event_heap[0].event if self._event_heap else None

    def get_next_event(self) -> Optional[Event]:
        next_event = self.peek_next_event()
        # If the next event is due, we can set it as the current event
        if next_event and (next_event.is_due() or self.current_event is None):
            if self.current_event and self.current_event.is_running:
                # If current event is running, we need to pause it
                self.current_event.is_running = False
            self.current_event = next_event
            heapq.heappop(self._event_heap) if next_event in self._event_heap else None
            self.update_priorities() 
        elif not self.current_event or self.current_event and self.current_event.is_completed:
            # If the current event is completed or not set, we can set the next event
            self.current_event = next_event
            heapq.heappop(self._event_heap) if next_event in self._event_heap else None
            self.update_priorities() 
        return self.current_event
    
    def skip_current_event(self) -> Optional[Event]:
        """
        Skips the current event and return the next event if available.
        If the current event is completed, it will be marked as such.
        """
        if self.current_event:
            self.current_event.is_completed = True
            self.current_event.is_running = False
            session_logger.info(f"Skipped event: {self.current_event.summary}")
            return self.get_next_event()
        else:
            session_logger.warning("No current event to skip.")
            return None
        
    def continue_current_event(self) -> None:
        """
        Starts or continues the current event if it is not running.
        """
        if self.current_event and not self.current_event.is_running:
            self.current_event.is_running = True
            session_logger.info(f"Started event: {self.current_event.summary}")
            self.current_event.notify()
        else:
            session_logger.warning("Current event is already running or not set.")  

    def pause_current_event(self) -> None:
        """
        Pauses the current event if it is running.
        """
        if self.current_event and self.current_event.is_running:
            self.current_event.is_running = False
            session_logger.info(f"Paused event: {self.current_event.summary}")
        else:
            session_logger.warning("Current event is not running or not set.")

    def event_list(self) -> Tuple[List[Any], List[Any]]:
        """
        Returns a list of all events in the coordinator.
        """
        completed = [event for event in self._instances.values() if event.is_completed]
        upcoming = [e.event for e in self._event_heap]
        return completed, upcoming



class EventTimer(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame | ctk.CTkScrollableFrame, controller: ctk.CTkFrame, event: Event, **kwargs: Any):
        super().__init__(master)
        self.controller = controller
        self.event = event
        self._update_job = None
        self.name_label = None
        self.timer_label = None
        self.status_label = None
        self.progress_bar = None

        self.show_counter()
        self.show_progress_bar()
        self.show_start_to_end()

    def show_counter(self)-> None:
        # event Name (Title)
        name = self.event.summary if self.event and self.event.summary else "Unnamed Event"
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
                text_color="#ffffff"
            )
            start_end_label.pack(pady=(2, 0), anchor="w", padx=(10, 10))

    def update_progress_bar(self) -> None:
        """
        Updates the progress bar based on the event's elapsed time and duration.
        If the event is running, it updates the elapsed time.
        """
        if self.event and self.event.is_running:
            self.event.elapsed_time += 1
            progress_value = self.event.elapsed_time / self.event.duration if self.event.duration > 0 else 1.0
            self.progress_bar.set(progress_value) if self.progress_bar else None 

    def update_counter_content(self) -> None:
        elapsed = time.strftime("%H : %M : %S", time.gmtime(self.event.elapsed_time)) if self.event else "00 : 00 : 00"
        duration = self.event.duration if self.event else None

        if self.event and self.event.is_completed:
            timer_text = elapsed
            status_text = "✔ Completed"
            timer_color = "#019751"
        elif self.event and self.event.is_running:
            self.event.elapsed_time += 1
            elapsed = time.strftime("%H : %M : %S", time.gmtime(self.event.elapsed_time))
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
        self.timer_label.configure(text=timer_text, text_color=timer_color) if self.timer_label else None
        self.status_label.configure(text=status_text) if self.status_label else None

        # Schedule next update
        self._update_job = self.after(1000, self.update_counter_content)

class EventCard(ctk.CTkFrame):
    def __init__(self, master, event: Event, index: int, fg_color="transparent", border_color="#292929", border_width=2):
        super().__init__(master, fg_color=fg_color, border_color=border_color, border_width=border_width)
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

        time_details = f"{self.event.start_time.strftime('%H:%M:%S') if self.event.start_time else 'N/A'} - {self.event.end_time.strftime('%H:%M:%S') if self.event.end_time else 'N/A'}"
        time_label = ctk.CTkLabel(
            self,
            text=time_details,
            font=ctk.CTkFont("Segoe UI", 10, "normal"),
            text_color="#747474"
        )
        time_label.grid(column=0, row=1, padx=(10, 10), pady=(5, 5), sticky="w")

        if self.event.is_completed:
            self.badge(self, "Completed").grid(
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
            state="disabled"
        )
    

class QueueList(ctk.CTkScrollableFrame):
    def __init__(self, master: ctk.CTkFrame | ctk.CTkScrollableFrame, coordinator: EventCoordinator, **kwargs: Any):
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
        completed, upcoming = self.coordinator.event_list()
        # create a comparable signature (summary strings only)
        completed_keys = [e._id for e in completed]
        upcoming_keys = [e._id for e in upcoming]

        if completed_keys != self._last_completed or upcoming_keys != self._last_upcoming:
            self.render(list(completed), list(upcoming))
            self._last_completed = completed_keys
            self._last_upcoming = upcoming_keys

        self.after(1000, self.on_load)  

class Spinner(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame | ctk.CTkScrollableFrame, **kwargs: Any):
        super().__init__(master, **kwargs)
        self.spinner = ctk.CTkLabel(self, text="Loading...", font=ctk.CTkFont("Segoe UI", 16, "bold"))
        self.spinner.pack(pady=(10, 0), padx=(10, 10))
        self.spinner.configure(text_color="#585858")
        self.after(1000, self.update_spinner)

    def update_spinner(self) -> None:
        self.spinner.configure(text="Please wait...")   


class EventsView(ctk.CTkFrame):
    def __init__(self, master, controller, service_manager, coordinator=EventCoordinator, **kwargs: Any):
        super().__init__(master, **kwargs)
        self.coordinator = coordinator()
        self.service_manager = service_manager
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
        self.controls_container.grid(column=0, row=2, pady=(5, 10), padx=10, sticky="new")
        self.controls_container.columnconfigure((0, 1, 2), weight=1)



        self.queue_list = QueueList(self.queue_section, self.coordinator)
        self.queue_list.grid(column=0, row=1, pady=(5, 5), padx=10, sticky="nsew")

        self.build_controls()
        self.refresh()
    
    def build_section(self, title: Optional[str]=None, scrollable: bool=False) -> ctk.CTkFrame | ctk.CTkScrollableFrame: 
        """
        Builds a section with a title and a frame.
        Args:
            title (str): The title of the section.
            section (ctk.CTkFrame): The frame to display in the section.
        """
        if scrollable:
            section = ctk.CTkScrollableFrame(self, fg_color="transparent", border_color="#292929", border_width=2)
        else:
            section = ctk.CTkFrame(self, fg_color="transparent", border_color="#292929", border_width=2)
        if title:
            lbl_container = ctk.CTkFrame(section, fg_color="transparent")
            lbl_container.grid(row=0, column=0, sticky="nsew", padx=(10, 10))
            lbl_container.columnconfigure(0, weight=1)
            label = ctk.CTkLabel(
                lbl_container,
                text=title,
                font=ctk.CTkFont("Segoe UI", 12, "normal"),
                text_color="#ffffff"
            )
            label.grid(pady=(5, 0), padx=(10, 10), row=0, column=0, sticky="w")
        section.grid(padx=10, sticky="nsew", pady=10)
        section.grid_rowconfigure(1, weight=1)
        return section


    def build_controls(self):
        self.start_button = ctk.CTkButton(
            self.controls_container, text="Start", fg_color="#007f44",
            command=self.coordinator.continue_current_event
        )
        self.start_button.grid(column=0, row=0, padx=5, pady=5, sticky="ew")

        self.pause_button = ctk.CTkButton(
            self.controls_container, text="Pause", fg_color="#C4B101", text_color="#747474",
            command=self.coordinator.pause_current_event
        )
        self.pause_button.grid(column=1, row=0, padx=5, pady=5, sticky="ew")

        self.skip_button = ctk.CTkButton(
            self.controls_container, text="Skip", fg_color="#880000",
            text_color="#E6E6E6",
            command=self.skip_current_event
        )
        self.skip_button.grid(column=2, row=0, padx=5, pady=5, sticky="ew")

    def refresh(self):
        next_event = self.coordinator.get_next_event()

        if next_event and self.current_event and next_event._id == self.current_event._id:
            return self.after(1000, self.refresh)
        if self.current_event:
            for widget in self.timer_section.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and any(
                    isinstance(child, ctk.CTkLabel) and child.cget("text") == "Current Event"
                    for child in widget.winfo_children()
                ):
                    continue
                if isinstance(widget, EventTimer) and isinstance(widget.event, Event):
                    if next_event and widget.event._id == next_event._id:
                        widget.tkraise()
                        return self.after(1000, self.refresh)
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Loading...":
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
        if new_event:
            self.load_event(new_event)
