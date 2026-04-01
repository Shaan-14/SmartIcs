# SmartCal — Repository File Structure

```
GROUP-PROJECT-GROUP52-SMARTICS/
│
├── main.py                         # CLI entry point, runs the full pipeline
├── config.py                       # API keys loaded from .env
├── requirements.txt
├── .env                            # API keys (gitignored)
├── .gitignore
├── README.md
│
├── models/
│   └── event.py                    # Event class, unchanged from full design
│
├── services/
│   ├── syllabus_parser.py          # Reads a local .txt or .pdf, calls Gemini
│   ├── sport_schedule_fetcher.py   # Calls sports API, returns game Events
│   ├── study_block_generator.py    # Calls Gemini, returns study block Events
│   └── calendar_manager.py        # Writes .ics file locally instead of Google Calendar
│
├── utils/
│   ├── ical_formatter.py           # Event → .ics format
│   └── time_utils.py               # Datetime helpers, waking hour clamping
│
└── tests/
    ├── test_event.py
    ├── test_syllabus_parser.py
    ├── test_sport_fetcher.py
    └── test_study_generator.py
```

## Key dependency notes

- `flask` — web framework
- `google-auth`, `google-auth-oauthlib`, `google-api-python-client` — Google Calendar + OAuth2
- `icalendar` — .ics formatting before Calendar API writes
- `google-generativeai` — Gemini API (SyllabusParser + StudyBlockGenerator)
- `requests` — TheSportsDB / SportsRadar API calls
- `python-dotenv` — loads `.env` into `config.py`
- `pytest` — test runner
