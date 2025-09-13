from logging_config import session_logger
from dataclasses import dataclass
import uuid
from typing import Optional
import datetime
from plyer import notification


@dataclass
class Event:
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
    priority: int | float = 0

    def __post_init__(self) -> None:
        if isinstance(self.start_time, datetime.datetime) and isinstance(
            self.end_time, datetime.datetime
        ):
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
            return True
        return self.start_time <= datetime.datetime.now()

    def set_priority(self, priority):
        self.priority = priority
        return self

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
                session_logger.error(
                    f"Setting duration for scheduled event from {self.source} is not allowed."
                )
                return
            self.end_time = (
                self.start_time + datetime.timedelta(seconds=duration)
                if self.start_time
                else None
            )
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
            )  # type: ignore
            session_logger.info(f"Notification sent for event: {self.summary}")
        else:
            session_logger.warning("No summary provided for notification.")

    def __lt__(self, other):
        return self.priority < other.priority
