from dataclasses import dataclass, field
from src.event import Event
import threading
from typing import Any, Optional, Dict, List
from logging_config import session_logger
import heapq
import datetime


class Singleton_:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance


class EventCoordinator(Singleton_):
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        # shared state
        self._state_lock = threading.RLock()
        self._instances: Dict[str, Event] = {}
        self._event_heap: List[Event] = []
        self.current_event: Optional[Event] = None
        self.ui_list = set()

    def add_event(self, event: "Event") -> None:
        with self._state_lock:
            event.set_priority(self.calculate_priority(event))
            self._instances[event._id] = event
            self._event_heap.append(event)
            self._rebuild_heap()

    def remove_event(self, _id: "str") -> None:
        with self._state_lock:
            if _id in self._instances:
                event = self._instances.get(_id, None)
                del self._instances[_id]
                if self.current_event and event and event._id != self.current_event._id:
                    self._event_heap.remove(event)
            self._rebuild_heap()

    def check_state(self, event: Event):
        is_completed = event.is_completed
        ended = (
            isinstance(event.end_time, datetime.datetime)
            and event.end_time < datetime.datetime.now()
        )
        return is_completed or ended

    def _rebuild_heap(self) -> None:
        with self._state_lock:
            heapq.heapify(self._event_heap)

    def calculate_priority(self, event: "Event") -> float:
        """
        Calculates the priority of the event.
        """
        now = datetime.datetime.now()

        if event.start_time:
            seconds_until_start = (event.start_time - now).total_seconds()
            return seconds_until_start

        # unscheduled: sooner-to-finish first
        duration = float(getattr(event, "duration", 0.0) or 0.0)
        elapsed = float(getattr(event, "elapsed_time", 0.0) or 0.0)
        remaining = max(duration - elapsed, 0.0)
        return remaining

    def peek_next_event(self) -> Optional["Event"]:
        return self._event_heap[0] if self._event_heap else None

    def get_next_event(self) -> Optional["Event"]:
        next_event = self.peek_next_event()

        if (
            self.current_event is None
            or self.current_event.is_completed
            or self.current_event.end_time
            and self.current_event.end_time < datetime.datetime.now()
        ):
            self.current_event = next_event
            if self.current_event:
                heapq.heappop(self._event_heap)
        else:
            if self.current_event.is_running and self.current_event.is_scheduled:
                return self.current_event
            elif next_event and next_event.is_due():
                self.current_event.is_running = False
                self.current_event = next_event
                heapq.heappop(self._event_heap)
        self._rebuild_heap()
        return self.current_event

    # ---------- controls ----------
    def skip_current_event(self) -> Optional[Event]:
        if self.current_event:
            self.current_event.is_running = False
            session_logger.info(f"Skipped event: {self.current_event.summary}")
        return self.get_next_event()

    def upcoming_list(self) -> List["Event"]:
        return [event for event in self._event_heap]

    def completed_list(self) -> List["Event"]:
        completed = [e for e in self._instances.values() if self.check_state(e)]
        return completed
