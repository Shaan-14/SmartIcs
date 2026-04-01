'''
Unit tests for the SportScheduleFetcher service.
Uses mocked API responses to test game schedule retrieval,
raw data mapping to Event objects, and supported league listing.
creates a .ics file with the fetched events to verify correct formatting and integration with CalendarManager.
'''
from services.sport_schedule_fetcher import SportScheduleFetcher
from models.event import Event
from utils.ical_formatter import ICalFormatter

if __name__ == "__main__":
    fetcher = SportScheduleFetcher()
    leagues = fetcher.get_supported_leagues()
    print("Supported leagues:", leagues)
    print()
    print("Select League:")
    for i in range(len(leagues)):
        print(f"{i+1}. {leagues[i]}")
    inp = leagues[int(input()) - 1]
    teams = fetcher.list_teams(inp)
    print("TEAM:   |    ID:")
    for t in teams.items():
        print(f"{t[0]}: {t[1]}")
    