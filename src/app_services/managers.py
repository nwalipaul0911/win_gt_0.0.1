from .interfaces import Service
from typing import Dict, Optional
from abc import ABC, abstractmethod

# === ServiceManager (Singleton per platform) ===
class BaseServiceManager(ABC):
    _instances: Dict[str, Service] = {}
    _registry: Dict[str, Dict[str, Service]] = {}
    _singleton = None

    @classmethod
    @abstractmethod
    def register(cls, platform:str, service_name: str, service_cls: Service) -> 'BaseServiceManager':
        ...
    
    @classmethod
    @abstractmethod
    def get_service(cls, platform: str, service_name: str) -> Optional[Service]:
        ... 


class ServiceManager(BaseServiceManager):
    def __new__(cls):
        if not cls._singleton:
            cls._singleton = super().__new__(cls)
        return cls._singleton
    
    def __init__(self):
        if hasattr(self, "_instantiated") and self._instantiated:
            return
        self._instantiated = True

    @classmethod
    def register(cls, platform: str, service_name: str, service_cls: Service) -> BaseServiceManager:
        platform = platform.lower()
        if platform not in cls._registry:
            cls._registry[platform] = {service_name: service_cls}
        else:
            if service_name in cls._registry[platform]:
                raise ValueError(f"Service {service_name} already registered for platform {platform}")
            cls._registry[platform][service_name] = service_cls
        return ServiceManager()

    @classmethod
    def get_service(cls, platform: str, service_name: str) -> Optional[Service]:
        platform = platform.lower()
        if platform not in cls._instances:
            if platform not in cls._registry:
                raise ValueError(f"Unsupported platform: {platform}")
            service = cls._registry[platform].get(service_name, None)
            if service is not None:
                cls._instances[service_name] = service
        return cls._instances[service_name]
    
    @classmethod
    def get_all_services(cls, service: str) -> Dict[str, Service]:
        """Returns all matching services for a given service name."""
        services = {}
        for platform, service_dict in cls._registry.items():
            if service in service_dict:
                services[platform] = service_dict[service]
        return services
            
