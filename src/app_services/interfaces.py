from abc import ABCMeta, ABC, abstractmethod
from typing import Dict, Optional, List, Any
# === Base Authenticator Interface ===
class Authenticator(ABC):
    @abstractmethod
    def authenticate(self):
        """Perform platform-specific authentication."""
        ...

    @abstractmethod
    def is_authenticated(self) -> bool:
        ...


class Service(ABCMeta):
    @abstractmethod
    def get_service_data(self) -> List[dict[str, Any]]:
        ...

    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if the service is authenticated.
        Returns True if authenticated, False otherwise.
        """
        ...