from src.app_services.interfaces import Authenticator, Service
from logging_config import session_logger
import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import Any, List, Dict, Optional
import dateutil.parser as date_parser


class GoogleAuthenticator(Authenticator):
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    CLIENT_SECRET = "credentials.json"

    def __init__(self) -> None:
        self.__creds = None

    def authenticate(self) -> bool:
        if os.path.exists("auth.json"):
            self.__creds = Credentials.from_authorized_user_file("auth.json")
        if not self.is_authenticated():
            flow = InstalledAppFlow.from_client_secrets_file(
                self.CLIENT_SECRET, self.SCOPES
            )
            self.__creds = flow.run_local_server(port=0)
            with open("auth.json", "w") as auth_file:
                auth_file.write(self.__creds.to_json())
                return True
        return False

    def is_authenticated(self) -> bool:
        if self.__creds and self.__creds.valid:
            return True
        if self.__creds and self.__creds.expired and self.__creds.refresh_token:
            try:
                self.__creds.refresh(Request())
                return self.__creds.valid if self.__creds else False
            except Exception:
                return False
        return False

    def get_service(self, service_name: str, version: str) -> Any:
        if not self.is_authenticated():
            self.authenticate()
        return build(service_name, version, credentials=self.__creds)


class GoogleCalendarService(GoogleAuthenticator, metaclass=Service):
    def __init__(self) -> None:
        super().__init__()

    def get_service_data(self, num: int = 10) -> Optional[List[dict[str, Any]]]:
        service = self.get_service("calendar", version="v3")
        parsed_events: Optional[List[Dict[str, Any]]] = []
        if service is not None:
            now = datetime.datetime.now(datetime.timezone.utc)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            session_logger.info("Fetching events from Google calender")
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=end_of_day.isoformat(),
                    maxResults=num,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            parsed_events = list(
                map(lambda data: self.parse_calendar_data(data=data), events)
            )

        return parsed_events

    def parse_calendar_data(self, data: Dict[str, Any]) -> dict[str, Any]:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        start = data["start"].get("dateTime", now)
        end = data["end"].get("dateTime", now)

        data["start"] = date_parser.parse(start).replace(tzinfo=None)
        data["end"] = date_parser.parse(end).replace(tzinfo=None)
        return data
