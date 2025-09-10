from dataclasses import dataclass, field
from src.event import Event
import threading
from typing import Any, Optional, Dict, List
from logging_config import session_logger
import heapq
import datetime


class Coordinator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance


@dataclass(order=True)
class PrioritizedEvent:
    priority: float
    event: Event = field(compare=False)


class EventCoordinator(Coordinator):
    _loader_started = False
    _loader_lock = threading.Lock()

    def __init__(self, **kwargs: Any):
        if getattr(self, "_initialized", False):
            return

        # shared state
        self._state_lock = threading.RLock()
        self._instances: Dict[str, Event] = {}
        self._event_heap: List[PrioritizedEvent] = []
        self.current_event: Optional[Event] = None
        self._initialized = True
        self.ui_list = set()

    # ---------- event state / heap ----------
    def add_event(self, event: "Event") -> None:
        with self._state_lock:
            self._instances[event._id] = event
            self._rebuild_heap(list(self._instances.values()))

    def remove_event(self, event: "Event") -> None:
        with self._state_lock:
            if event._id in self._instances:
                del self._instances[event._id]
            self._rebuild_heap(list(self._instances.values()))

    def check_state(self, event: Event):
        is_completed = event.is_completed
        ended = (
            isinstance(event.end_time, datetime.datetime)
            and event.end_time < datetime.datetime.now()
        )
        return is_completed or ended

    def _rebuild_heap(self, events: List["Event"]) -> None:
        with self._state_lock:
            self._event_heap = [
                PrioritizedEvent(self.event_priority(e), e)
                for e in events
                if not self.check_state(e)
            ]
            heapq.heapify(self._event_heap)

    def update_priorities(self) -> None:
        self._rebuild_heap(list(self._instances.values()))

    def event_priority(self, event: "Event") -> float:
        now = datetime.datetime.now()

        if event.start_time:
            seconds_until_start = (event.start_time - now).total_seconds()
            # events already started get highest priority \
            # (negative time -> run now)
            return seconds_until_start

        # unscheduled: sooner-to-finish first
        duration = float(getattr(event, "duration", 0.0) or 0.0)
        elapsed = float(getattr(event, "elapsed_time", 0.0) or 0.0)
        remaining = max(duration - elapsed, 0.0)
        return remaining

    def peek_next_event(self) -> Optional["Event"]:
        return self._event_heap[0].event if self._event_heap else None

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
            elif (
                self._event_heap
                and next_event
                and next_event.is_scheduled
                and next_event.is_due()
            ):
                self.current_event.is_running = False
                self.current_event = next_event
                heapq.heappop(self._event_heap)
        self._rebuild_heap([pe.event for pe in self._event_heap])
        return self.current_event

    # ---------- controls ----------
    def skip_current_event(self) -> Optional[Event]:
        if self.current_event:
            self.current_event.is_running = False
            session_logger.info(f"Skipped event: {self.current_event.summary}")
        return self.get_next_event()

    def upcoming_list(self) -> List["Event"]:
        return [pe.event for pe in self._event_heap]

    def completed_list(self) -> List["Event"]:
        completed = [e for e in self._instances.values() if self.check_state(e)]
        return completed
