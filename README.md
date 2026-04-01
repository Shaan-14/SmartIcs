# SmartIcs — AI-Powered Student Calendar

SmartIcs automatically organizes your academic deadlines, everyday events, and favourite sports team schedules into a personalized calendar — avoiding conflicts and generating smart study blocks.

---

## Team

- **Shaan Wrench** — Google Gemini API (syllabus parsing + study block generation), Google Calendar API
- **Mats Leis** — TheSportsDB / SportsRadar API, Google Calendar API

---

## Features

- Parse syllabi from PDF or text using Gemini AI
- Fetch live sports schedules for your favourite teams
- Generate AI-powered study blocks around your schedule
- Export to Google Calendar or a local `.ics` file
- Color-coded events (red = exams, blue = assignments, green = games, teal = study blocks)

---

## Requirements

- Python 3.10+
- A Google Account
- A Gemini API key (linked to Google Cloud billing)
- Google Calendar API credentials

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ShaimaaAliECE/group-project-smartics.git
cd group-project-smartics
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your Gemini API key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **Get API key** → **Create API key**
4. When prompted, select your Google Cloud project (recommended to link to a billing account for higher quotas)
5. Copy the API key
6. Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

### 4. Set up Google Calendar API credentials

This step allows SmartIcs to write events directly to your Google Calendar.

#### Step 1 — Enable the Google Calendar API

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Select your project (or create a new one)
3. Go to **APIs & Services** → **Enable APIs and Services**
4. Search for **Google Calendar API** and click **Enable**

#### Step 2 — Create OAuth2 credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted, configure the consent screen first:
   - Choose **External**
   - Fill in app name (e.g. SmartIcs) and your email
   - Click **Save and Continue** through all steps
4. Back in Credentials, click **+ Create Credentials** → **OAuth client ID**
5. Application type: **Desktop App**
6. Name: **SmartIcs**
7. Click **Create**
8. Click **Download JSON** on the confirmation screen
9. Rename the downloaded file to `credentials.json`
10. Place `credentials.json` in the **root of the project** (same folder as `main.py`)

#### Step 3 — First-time sign in

When you run SmartIcs for the first time and choose to push to Google Calendar:
- A browser window will open asking you to sign in with Google
- Click **Advanced** → **Go to SmartIcs (unsafe)** (this is safe — it's your own app)
- Click **Allow** to grant calendar access
- A `token.json` file will be saved automatically so you won't need to sign in again

---

## Running the App

```bash
python main.py
```

Follow the interactive prompts to:
1. Parse your syllabus (PDF or text)
2. Add manual events
3. Select your favourite sports teams
4. Generate AI study blocks
5. Export to Google Calendar or `.ics` file

---

## Project Structure

```
group-project-smartics/
├── models/
│   └── event.py                  # Shared Event data model
├── services/
│   ├── syllabus_parser.py        # Gemini API — parses syllabi
│   ├── study_block_generator.py  # Gemini API — generates study blocks
│   ├── calendar_manager.py       # Google Calendar API
│   └── sport_schedule_fetcher.py # SportsDB/SportsRadar API
├── tests/
├── utils/
├── main.py                       # CLI entry point
├── config.py
├── requirements.txt
├── .env                          # API keys (not tracked by git)
├── credentials.json              # Google OAuth credentials (not tracked by git)
└── token.json                    # Auto-generated after sign-in (not tracked by git)
```

---

## Notes

- `.env`, `credentials.json`, and `token.json` are all listed in `.gitignore` and will never be pushed to GitHub
- Each user must set up their own `.env` and `credentials.json` by following the steps above
- The `token.json` file is generated automatically after your first Google sign-in
