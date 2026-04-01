'''
Handles all calendar output for the SmartIcs application.
In the CLI MVP, writes the final merged list of Events to a local .ics file.
Intended to be upgraded to live Google Calendar API writes in the full release.
'''

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from models.event import Event

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'token.json')


def get_calendar_service():
    '''
    Handles OAuth2 authentication and returns a Google Calendar service object.
    Opens browser for login on first run, then saves token for future use.
    '''
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)
def create_calendar(service, name):
    '''
    Creates a new calendar in the student's Google Calendar account.
    Returns the calendar ID.
    '''
    calendar = {
        'summary': name,
        'timeZone': 'America/Toronto'
    }
    created = service.calendars().insert(body=calendar).execute()
    print(f"Created calendar: {created['summary']} (ID: {created['id']})")
    return created['id']


def add_event(service, event, calendar_id, color_id=None):
    '''
    Adds a single Event object to the specified Google Calendar.
    color_id: 1=blue, 2=green, 3=purple, 4=red, 5=yellow, 6=orange, 7=teal
    '''
    body = {
        'summary': event.title,
        'description': event.description or '',
        'start': {
            'dateTime': event.start_time.isoformat(),
            'timeZone': 'America/Toronto'
        },
        'end': {
            'dateTime': event.end_time.isoformat(),
            'timeZone': 'America/Toronto'
        }
    }

    if color_id:
        body['colorId'] = str(color_id)

    created = service.events().insert(calendarId=calendar_id, body=body).execute()
    print(f"Added: {event.title} on {event.start_time.date()}")
    return created


def sync_all(events, calendar_name="SmartIcs"):
    '''
    Main function - takes a list of all Event objects, creates a SmartIcs
    calendar, and pushes everything to Google Calendar with color coding:
    - Red (4): Exams, tests, quizzes, finals
    - Blue (1): Assignments and deadlines
    - Green (2): Sports games
    - Teal (7): Study blocks
    '''
    service = get_calendar_service()
    calendar_id = create_calendar(service, calendar_name)

    counts = {"academic": 0, "sports": 0, "study": 0}

    for event in events:
        title_lower = event.title.lower()
        source = event.source or ""

        if source == "study_block_generator":
            color_id = 7  # teal
            counts["study"] += 1
        elif any(word in title_lower for word in ["game", "vs", "nhl", "nba", "mlb", "nfl"]):
            color_id = 2  # green
            counts["sports"] += 1
        elif any(word in title_lower for word in ["exam", "test", "quiz", "final", "midterm"]):
            color_id = 4  # red
            counts["academic"] += 1
        else:
            color_id = 1  # blue
            counts["academic"] += 1

        add_event(service, event, calendar_id, color_id)

    print(f"\n SmartIcs created successfully!")
    print(f"   Academic events: {counts['academic']}")
    print(f"   Sports games: {counts['sports']}")
    print(f"   Study blocks: {counts['study']}")
    print(f"   Total: {len(events)} events added to Google Calendar")