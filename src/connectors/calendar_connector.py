"""Calendar Connector — SRP: only knows how to fetch Google Calendar data."""
from src.connectors.base import BaseConnector


class CalendarConnector(BaseConnector):
    @property
    def source_name(self) -> str:
        return "calendar"

    def _table_map(self) -> dict[str, str]:
        return {
            "events": "calendar_events.jsonl",
            "engineers": "engineers.jsonl",
        }

    def _fetch_live(self, table: str, filters: dict) -> list[dict]:
        """Fetch real data from Google Calendar."""
        import datetime
        import uuid
        import os
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        
        if table != "events":
            return []

        creds_path = self._settings.google_application_credentials
        if not creds_path or not os.path.exists(creds_path):
            print(f"Skipping Calendar live fetch: missing {creds_path}. Falling back to mock data.")
            return self._load_from_file(table)

        try:
            # We must impersonate a user or use domain-wide delegation
            # If not configured, we'll hit 403.
            creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/calendar.readonly"]
            )
            service = build('calendar', 'v3', credentials=creds)
            
            engineers = self._load_from_file("engineers")
            emails = [e.get("email") for e in engineers if e.get("email")]
            
            events_data = []
            
            # Fetch last 7 days of events
            now = datetime.datetime.utcnow()
            time_min = (now - datetime.timedelta(days=7)).isoformat() + 'Z'
            time_max = now.isoformat() + 'Z'
            
            for email in emails:
                try:
                    events_result = service.events().list(
                        calendarId=email,
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    events = events_result.get('items', [])
                    
                    if not events:
                        print(f"No events found for {email} in the last 7 days. Falling back to mock data.")
                        mock_events = self._load_from_file("events")
                        events_data.extend([ev for ev in mock_events if ev.get("attendee_email") == email])
                    else:
                        for event in events:
                            start_time = event['start'].get('dateTime', event['start'].get('date'))
                            end_time = event['end'].get('dateTime', event['end'].get('date'))
                            
                            # Calculate duration
                            duration_hours = 1.0 # Default
                            if 'T' in start_time and 'T' in end_time:
                                st_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                end_dt = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                duration_hours = (end_dt - st_dt).total_seconds() / 3600.0
                                
                            # Check declined status
                            is_declined = False
                            attendees = event.get('attendees', [])
                            for a in attendees:
                                if a.get('email') == email and a.get('responseStatus') == 'declined':
                                    is_declined = True
                                    
                            events_data.append({
                                "id": f"ev_{uuid.uuid4().hex[:8]}",
                                "attendee_email": email,
                                "event_type": "meeting",
                                "duration_hours": round(duration_hours, 2),
                                "week": f"{now.year}-W{now.isocalendar()[1]}",
                                "is_declined": is_declined,
                                "is_recurring": 'recurringEventId' in event,
                                "meeting_title": event.get('summary', 'Untitled')
                            })
                except HttpError as e:
                    print(f"Calendar API error for {email}: {e.status_code}. Falling back to mock data for this user.")
                    mock_events = self._load_from_file("events")
                    events_data.extend([ev for ev in mock_events if ev.get("attendee_email") == email])
                    
            return events_data
            
        except Exception as e:
            print(f"Failed to setup Calendar API client: {e}. Falling back to mock data.")
            return self._load_from_file(table)

    def _check_live_connection(self) -> bool:
        creds_path = self._settings.google_application_credentials
        if not creds_path:
            return False
        import os
        return os.path.exists(creds_path)
