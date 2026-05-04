'''
SmartIcs Flask Backend
Wires all existing services (syllabus parser, sports fetcher, study block generator,
calendar manager) into a web API. Handles Google OAuth2 redirect flow for the web.
'''

import os
import json
import tempfile
from datetime import datetime

from flask import (
    Flask, jsonify, render_template, request,
    redirect, url_for, session, Response
)
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from services.sport_schedule_fetcher import SportScheduleFetcher, LEAGUE_MAP
from services.syllabus_parser import parse_syllabus, parse_pdf
from services.study_block_generator import generate_study_blocks
from models.event import Event

# ── App setup ──────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = 'smartics-dev-secret-key-change-in-production'

fetcher = SportScheduleFetcher()

SCOPES           = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')
TOKEN_FILE       = os.path.join(os.path.dirname(__file__), 'token.json')

# Allow HTTP for local dev — remove this line before deploying to production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


# ── Helpers ────────────────────────────────────────────────────────────────────

def events_from_json(data):
    '''Converts a list of serialised event dicts back into Event objects.'''
    events = []
    for d in data:
        try:
            e = Event(
                title=d['title'],
                start_time=datetime.fromisoformat(d['start_time']),
                end_time=datetime.fromisoformat(d['end_time']),
                description=d.get('description'),
                source=d.get('source'),
            )
            if d.get('reoccuring'):
                e.reoccuring = d['reoccuring']
            events.append(e)
        except Exception as ex:
            print(f'[WARN] Could not deserialise event: {ex}')
    return events


def get_calendar_service():
    '''Returns an authenticated Google Calendar service, or None if not authed.'''
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    if not creds or not creds.valid:
        return None
    return build('calendar', 'v3', credentials=creds)


# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── Sports ─────────────────────────────────────────────────────────────────────

@app.route('/api/leagues')
def get_leagues():
    return jsonify(list(LEAGUE_MAP.keys()))


@app.route('/api/teams/<league>')
def get_teams(league):
    league = league.upper()
    if league not in LEAGUE_MAP:
        return jsonify({'error': f'Unsupported league: {league}'}), 400
    teams = fetcher.list_teams(league)
    if teams is None:
        return jsonify({'error': 'Failed to fetch teams from ESPN'}), 502
    return jsonify(sorted(teams.keys()))


@app.route('/api/schedule', methods=['POST'])
def get_schedule():
    data      = request.json
    team_name = data.get('team')
    league    = data.get('league')
    if not team_name or not league:
        return jsonify({'error': 'team and league are required'}), 400
    events = fetcher.fetch_schedule(team_name, league)
    return jsonify([e.serialize() for e in events])


# ── Syllabus parsing ───────────────────────────────────────────────────────────

@app.route('/api/parse_text', methods=['POST'])
def parse_text():
    '''Parses raw pasted syllabus text via Gemini.'''
    data = request.json
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        events = parse_syllabus(text)
        return jsonify([e.serialize() for e in events])
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500


@app.route('/api/parse_pdf', methods=['POST'])
def parse_pdf_route():
    '''Accepts a PDF upload, saves it temporarily, and parses it via Gemini.'''
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are accepted'}), 400

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name
    try:
        events = parse_pdf(tmp_path)
        return jsonify([e.serialize() for e in events])
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500
    finally:
        os.unlink(tmp_path)


# ── Study blocks ───────────────────────────────────────────────────────────────

@app.route('/api/study_blocks', methods=['POST'])
def study_blocks():
    '''
    Accepts a combined list of serialised events (academic + sports)
    and returns AI-generated study blocks from study_block_generator.py.
    '''
    data       = request.json
    raw_events = data.get('events', [])
    if not raw_events:
        return jsonify({'error': 'No events provided'}), 400
    try:
        events = events_from_json(raw_events)
        blocks = generate_study_blocks(events)
        return jsonify([b.serialize() for b in blocks])
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500


# ── Google OAuth2 ──────────────────────────────────────────────────────────────

@app.route('/auth/google')
def auth_google():
    if not os.path.exists(CREDENTIALS_FILE):
        return jsonify({'error': 'credentials.json not found — see README.'}), 500

    import secrets, hashlib, base64
    code_verifier  = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('auth_callback', _external=True)
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        code_challenge=code_challenge,
        code_challenge_method='S256'
    )
    session['oauth_state']    = state
    session['code_verifier']  = code_verifier
    session.modified = True
    return redirect(auth_url)


@app.route('/auth/callback')
def auth_callback():
    code_verifier = session.get('code_verifier')
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        state=session.get('oauth_state'),
        redirect_uri=url_for('auth_callback', _external=True)
    )
    flow.fetch_token(
        authorization_response=request.url,
        code_verifier=code_verifier
    )
    with open(TOKEN_FILE, 'w') as f:
        f.write(flow.credentials.to_json())

    return redirect('/?auth=success')


@app.route('/auth/status')
def auth_status():
    '''Frontend polls this to check if Google Calendar is connected.'''
    service = get_calendar_service()
    return jsonify({'authenticated': service is not None})


@app.route('/auth/logout')
def auth_logout():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    return jsonify({'status': 'logged out'})


# ── Export ─────────────────────────────────────────────────────────────────────

@app.route('/api/export/ics', methods=['POST'])
def export_ics():
    '''Returns a downloadable .ics file built from the provided events.'''
    data       = request.json
    raw_events = data.get('events', [])
    if not raw_events:
        return jsonify({'error': 'No events to export'}), 400

    events = events_from_json(raw_events)
    lines  = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//SmartIcs//SmartIcs//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
    ]
    for e in events:
        lines.append(e.to_ical().strip())
    lines.append('END:VCALENDAR')

    return Response(
        '\n'.join(lines),
        mimetype='text/calendar',
        headers={'Content-Disposition': 'attachment; filename=smartics.ics'}
    )


@app.route('/api/export/gcal', methods=['POST'])
def export_gcal():
    '''
    Pushes all events to Google Calendar using the same colour-coding as
    calendar_manager.sync_all(). Requires /auth/google to have been completed.
    '''
    service = get_calendar_service()
    if not service:
        return jsonify({
            'error': 'Not authenticated with Google Calendar.',
            'auth_url': url_for('auth_google', _external=True)
        }), 401

    data           = request.json
    raw_events     = data.get('events', [])
    calendar_name  = data.get('calendar_name', 'SmartIcs')

    if not raw_events:
        return jsonify({'error': 'No events to export'}), 400

    events = events_from_json(raw_events)

    cal_body     = {'summary': calendar_name, 'timeZone': 'America/Toronto'}
    created_cal  = service.calendars().insert(body=cal_body).execute()
    calendar_id  = created_cal['id']

    counts = {'academic': 0, 'sports': 0, 'study': 0}
    for event in events:
        title_lower = event.title.lower()
        source      = event.source or ''

        if source == 'study_block_generator':
            color_id = '7'; counts['study'] += 1
        elif any(w in title_lower for w in ['game', 'vs', 'nhl', 'nba', 'mlb', 'nfl']):
            color_id = '2'; counts['sports'] += 1
        elif any(w in title_lower for w in ['exam', 'test', 'quiz', 'final', 'midterm']):
            color_id = '4'; counts['academic'] += 1
        else:
            color_id = '1'; counts['academic'] += 1

        body = {
            'summary':     event.title,
            'description': event.description or '',
            'colorId':     color_id,
            'start': {'dateTime': event.start_time.isoformat(), 'timeZone': 'America/Toronto'},
            'end':   {'dateTime': event.end_time.isoformat(),   'timeZone': 'America/Toronto'},
        }
        if getattr(event, 'reoccuring', None):
            body['recurrence'] = [f'RRULE:{event.reoccuring}']

        service.events().insert(calendarId=calendar_id, body=body).execute()

    return jsonify({'status': 'success', 'calendar_name': calendar_name,
                    'counts': counts, 'total': len(events)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
