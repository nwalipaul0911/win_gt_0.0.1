import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from src.app_services.managers import ServiceManager
import threading
from src.event import Event
from typing import Optional
from logging_config import session_logger
from src.coordinator import EventCoordinator


class ServiceLoader:
    _loader_started = False
    _loader_lock = threading.Lock()

    def __init__(self) -> None:
        # sync primitives
        self._stop_event = threading.Event()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: list[Future] = []
        self._state_lock = threading.RLock()
        self.coordinator = None
        self._data = {}
        self._initialized = True
        self.run_loader()

    def run_loader(self):
        with self._loader_lock:
            if not self.__class__._loader_started:
                self.__class__._loader_started = True
                threading.Thread(target=self._start_pollers, daemon=True).start()

    def _start_pollers(self):
        services = ServiceManager().get_integrated_services("calendar")
        if not services:
            session_logger.warning("No calendar services available.")
            return

        self._executor = ThreadPoolExecutor(max_workers=len(services))
        self._futures = [
            self._executor.submit(self._poll_service, platform, service)
            for platform, service in services.items()
        ]

    def _poll_service(self, platform: str, service):
        instance = service
        while not self._stop_event.is_set():
            try:
                events = instance.get_service_data()
                if events and events != self._data.get(platform, {}):
                    with self._state_lock:
                        self._data[platform] = events
                    for event_data in events:
                        event = Event(
                            _id=event_data.get("id", str(uuid.uuid4())),
                            summary=event_data.get("summary", "Unnamed Event"),
                            start_time=event_data.get("start"),
                            end_time=event_data.get("end"),
                            source=platform,
                        )
                        (
                            self.coordinator.add_event(event)
                            if self.coordinator is not None
                            else 0
                        )
            except Exception as e:
                session_logger.error(
                    f"Error loading events from {platform} service: {e}"
                )
            finally:
                # wait up to 60s, exit early if stop was signaled
                for _ in range(60):
                    if self._stop_event.wait(1.0):
                        return

    def set_coordinator(self, coordinator: EventCoordinator) -> None:
        self.coordinator = coordinator

    def shutdown(self):
        self._stop_event.set()
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
