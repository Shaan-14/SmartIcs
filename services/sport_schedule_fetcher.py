'''
Fetches upcoming game schedules from the ESPN public API.
Takes a team name and league as input and returns a list of Event objects.
Handles team lookup, schedule fetching, and mapping raw data to the Event model.
'''
import requests
from datetime import datetime, timedelta
from models.event import Event
from zoneinfo import ZoneInfo


# Maps user-friendly league names to ESPN sport/league slugs
LEAGUE_MAP = {
    "NBA":  ("basketball", "nba"),
    "NFL":  ("football", "nfl"),
    "NHL":  ("hockey", "nhl"),
    "MLB":  ("baseball", "mlb"),
    "MLS":  ("soccer", "usa.1"),
    "EPL":  ("soccer", "eng.1"),
    "NCAAF": ("football", "college-football"),
    "NCAAB": ("basketball", "mens-college-basketball"),
}

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"


class SportScheduleFetcher:
    '''
    Fetches game schedules using the ESPN public API.
    No API key required.
    '''
    def get_team_id(self, team_name, sport, league):
        '''
        Searches ESPN for a team by name and returns its ESPN team ID.
        '''
        url = f"{BASE_URL}/{sport}/{league}/teams"
        response = requests.get(url, params={"limit": 100})
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch teams: {response.status_code}")
            return None

        teams = response.json().get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
        for entry in teams:
            team = entry.get('team', {})
            if team_name.lower() in team.get('displayName', '').lower():
                print(f"[OK] Found team: '{team['displayName']}' (id={team['id']})")
                return team['id']

        print(f"[ERROR] No team found matching '{team_name}'")
        return None
    def list_teams(self, league):
        url = f"{BASE_URL}/{LEAGUE_MAP[league][0]}/{LEAGUE_MAP[league][1]}/teams"
        response = requests.get(url, params={"limit": 100})
        team_list = {}
        if response.status_code != 200:
            print(f"[ERROR] Failed to fetch teams: {response.status_code}")
            return None
        teams = response.json().get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
        for entry in teams:
            team = entry.get("team",{})
            team_list[team['displayName']] = team['id']
        return team_list
            
    def fetch_schedule(self, team_name, league_key):
        '''
        Fetches the full season schedule for a team.
        Returns a list of Event objects sorted chronologically.
        Past games include final score in description.
        '''
        league_key = league_key.upper()
        if league_key not in LEAGUE_MAP:
            print(f"[ERROR] Unsupported league '{league_key}'. Supported: {list(LEAGUE_MAP.keys())}")
            return []

        sport, league = LEAGUE_MAP[league_key]
        team_id = self.get_team_id(team_name, sport, league)
        if not team_id:
            return []

        url = f"{BASE_URL}/{sport}/{league}/teams/{team_id}/schedule"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"[ERROR] Schedule fetch failed: {response.status_code}")
            return []

        data = response.json()
        games = data.get('events', [])
        if not games:
            print(f"[WARN] No games found for '{team_name}'")
            return []

        events = []
        for game in games:
            event = self._map_to_event(game)
            if event:
                events.append(event)

        events.sort(key=lambda e: e.start_time)
        print(f"[OK] Parsed {len(events)} games for '{team_name}'")
        return events

    def _map_to_event(self, raw):
        '''
        Maps a raw ESPN event dict to an Event object.
        Title uses the ESPN event name.
        Description includes venue, and score + status if finished.
        '''
        EASTERN = ZoneInfo("America/Toronto")
        try:
            title = raw.get('name', 'Unknown Game')
            date_str = raw.get('date')
            start_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            start_time = start_time.astimezone(EASTERN).replace(tzinfo=None)
            end_time = start_time + timedelta(hours=2, minutes=30)

            # Venue
            venue = 'TBD'
            competitions = raw.get('competitions', [])
            if competitions:
                comp = competitions[0]
                venue_data = comp.get('venue', {})
                venue = venue_data.get('fullName', 'TBD')

                # Score and status
                status = comp.get('status', {}).get('type', {}).get('description', '')
                description = f"Venue: {venue}"

                if status == 'Final':
                    competitors = comp.get('competitors', [])
                    scores = {c['team']['displayName']: c['score']['displayValue'] for c in competitors}
                    score_str = ' | '.join([f"{team}: {score}" for team, score in scores.items()])
                    description += f" | Final: {score_str}"
                else:
                    description += f" | Status: {status}"
            else:
                description = f"Venue: {venue}"

            event = Event(title=title, start_time=start_time, end_time=end_time, description=description)
            status_tag = "FINAL" if "Final" in description else "UPCOMING"
            print(f"  [{status_tag}] {title} — {start_time.strftime('%Y-%m-%d %H:%M')}")
            return event

        except Exception as e:
            print(f"[ERROR] Failed to map event: {e}")
            return None

    def get_supported_leagues(self):
        '''
        Returns a list of supported league keys.
        '''
        return list(LEAGUE_MAP.keys())

