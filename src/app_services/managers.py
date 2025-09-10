from .interfaces import Service
from typing import Dict, Optional, Type, Any, List
from abc import ABC, abstractmethod
from utils import ConfigManager


class BaseServiceManager(ABC):
    _registry: Dict[str, Dict[str, Service]] = (
        {}
    )  # platform → {service_name: service_cls}
    _singleton: Optional[Any] = None

    @classmethod
    @abstractmethod
    def register(
        cls, platform: str, service_name: str, service_cls: Service
    ) -> "BaseServiceManager": ...

    @classmethod
    @abstractmethod
    def get_service(cls, platform: str, service_name: str) -> Optional["Service"]: ...


class ServiceManager(BaseServiceManager):
    def __new__(cls) -> Any:
        if not cls._singleton:
            cls._singleton = super().__new__(cls)
        return cls._singleton

    def __init__(self) -> None:
        if getattr(self, "_instantiated", False):
            return
        self._instantiated = True
        self._integrations: Dict[str, List[str]] = {}  # platform → service_name
        self.load_integrations()

    @classmethod
    def register(
        cls, platform: str, service_name: str, service_cls: Service
    ) -> "ServiceManager":
        platform, service_name = platform.lower(), service_name.lower()
        cls._registry.setdefault(platform, {})
        if service_name in cls._registry[platform]:
            pass
        cls._registry[platform][service_name] = service_cls
        return ServiceManager()

    @classmethod
    def get_service(cls, platform: str, service_name: str) -> Optional["Service"]:
        platform = platform.lower()

        if platform not in cls._registry:
            raise ValueError(f"Unsupported platform: {platform}")

        service_cls = cls._registry[platform].get(service_name, None)
        if service_cls is None:
            return None
        return service_cls()

    def get_all_services(self, service_name: str) -> Dict[str, Optional[Service]]:
        """Returns all services across platforms matching a given service name."""
        results = {}
        for platform, service_dict in self._registry.items():
            if service_name in service_dict:
                results[platform] = self.get_service(platform, service_name)
        return results

    def save_integrations(self) -> None:
        config_manager = ConfigManager()
        config_manager.save_config({"integrations": self._integrations})

    def load_integrations(self) -> None:
        config = ConfigManager.load_config()
        self._integrations = config.get("integrations", {})

    def integrate(self, platform: str, service_name: str) -> bool:
        platform, service_name = platform.lower(), service_name.lower()
        service = self.get_service(platform, service_name)
        if service and service.authenticate():
            self._integrations[platform] = [*self._integrations[platform], service_name]
            self.save_integrations()
            return True
        return False

    def get_integrated_services(self, service_name: str) -> Dict[str, Service]:
        """
        Returns all currently integrated services.
        If *args are provided, only return those service names.
        Keyed by platform → Service instance.
        """
        integrated = {}

        for platform, services in self._integrations.items():
            if service_name not in services:
                continue  # skip services not in filter

            service = self.get_service(platform, service_name)
            if service:
                integrated[platform] = service

        return integrated
