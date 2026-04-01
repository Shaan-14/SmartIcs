'''
SmartIcs CLI — Main entry point for the SmartIcs application.
Orchestrates syllabus parsing, sports schedule fetching, study block generation,
and Google Calendar syncing through an interactive command-line interface.
'''

import os
import sys
from datetime import datetime

# ── Lazy imports with helpful error messages ──────────────────────────────────

def _import_modules():
    '''Import all project modules, printing clear errors if dependencies are missing.'''
    errors = []

    try:
        from models.event import Event
    except ImportError as e:
        errors.append(f"  • models/event.py: {e}")
        Event = None

    try:
        from services.syllabus_parser import parse_syllabus, parse_pdf
    except ImportError as e:
        errors.append(f"  • services/syllabus_parser.py: {e}")
        parse_syllabus = parse_pdf = None

    try:
        from services.sport_schedule_fetcher import SportScheduleFetcher, LEAGUE_MAP
    except ImportError as e:
        errors.append(f"  • services/sport_schedule_fetcher.py: {e}")
        SportScheduleFetcher = None
        LEAGUE_MAP = {}

    try:
        from services.study_block_generator import generate_study_blocks
    except ImportError as e:
        errors.append(f"  • services/study_block_generator.py: {e}")
        generate_study_blocks = None

    try:
        from services.calendar_manager import sync_all
    except ImportError as e:
        errors.append(f"  • services/calendar_manager.py: {e}")
        sync_all = None

    try:
        from methods import rrule_reocurring
    except ImportError as e:
        errors.append(f"  • methods.py: {e}")
        rrule_reocurring = None

    if errors:
        print("\n⚠️  Some modules could not be imported (missing dependencies or wrong paths):")
        for err in errors:
            print(err)
        print("\nContinuing with available modules...\n")

    return {
        "Event": Event,
        "parse_syllabus": parse_syllabus,
        "parse_pdf": parse_pdf,
        "SportScheduleFetcher": SportScheduleFetcher,
        "LEAGUE_MAP": LEAGUE_MAP,
        "generate_study_blocks": generate_study_blocks,
        "sync_all": sync_all,
        "rrule_reocurring": rrule_reocurring,
    }


# ── Display helpers ───────────────────────────────────────────────────────────

BANNER = r"""
  ____                       _   ___
 / ___| _ __ ___   __ _ _ __| ||_ _|___  ___
 \___ \| '_ ` _ \ / _` | '__| __|| |/ __|/ __|
  ___) | | | | | | (_| | |  | |_ | | (__ \__ \
 |____/|_| |_| |_|\__,_|_|   \__|___\___||___/

         Your AI-Powered Student Calendar
"""

def print_banner():
    print("\033[36m" + BANNER + "\033[0m")

def print_section(title):
    width = 50
    print(f"\n\033[33m{'─' * width}\033[0m")
    print(f"\033[33m  {title}\033[0m")
    print(f"\033[33m{'─' * width}\033[0m")

def print_success(msg):
    print(f"\033[32m✓ {msg}\033[0m")

def print_error(msg):
    print(f"\033[31m✗ {msg}\033[0m")

def print_info(msg):
    print(f"\033[34mℹ {msg}\033[0m")

def print_warning(msg):
    print(f"\033[33m⚠ {msg}\033[0m")

def prompt(text, default=None):
    '''Prompt the user, showing a default value if provided.'''
    suffix = f" [{default}]" if default else ""
    value = input(f"\033[1m{text}{suffix}: \033[0m").strip()
    return value if value else default

def confirm(text):
    '''Ask a yes/no question; return True for yes.'''
    answer = input(f"\033[1m{text} [y/N]: \033[0m").strip().lower()
    return answer in ("y", "yes")

def choose(text, options):
    '''
    Present a numbered menu and return the chosen option string.
    options: list of strings
    '''
    print(f"\033[1m{text}\033[0m")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input("\033[1mChoice: \033[0m").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx]
        print_error(f"Please enter a number between 1 and {len(options)}.")


def display_events(events, label="Events"):
    '''Pretty-print a list of Event objects in a table.'''
    if not events:
        print_warning(f"No {label.lower()} to display.")
        return

    print_section(f"{label} ({len(events)} total)")
    col_w = [40, 20, 20]
    header = f"  {'Title':<{col_w[0]}} {'Start':<{col_w[1]}} {'End':<{col_w[2]}}"
    print("\033[90m" + header + "\033[0m")
    print("\033[90m  " + "─" * (sum(col_w) + 2) + "\033[0m")

    for e in sorted(events, key=lambda x: x.start_time):
        title = e.title[:col_w[0] - 1]
        start = e.start_time.strftime("%Y-%m-%d %H:%M")
        end = e.end_time.strftime("%Y-%m-%d %H:%M") if e.end_time else "—"
        print(f"  {title:<{col_w[0]}} {start:<{col_w[1]}} {end:<{col_w[2]}}")


# ── Step handlers ─────────────────────────────────────────────────────────────

def step_syllabus(mods):
    '''Parse a syllabus from text or PDF and return a list of Events.'''
    parse_syllabus = mods["parse_syllabus"]
    parse_pdf = mods["parse_pdf"]

    if not parse_syllabus:
        print_error("Syllabus parser is unavailable (check dependencies).")
        return []

    print_section("Step 1 — Parse Syllabus")
    source = choose("How would you like to provide your syllabus?", [
        "Paste syllabus text",
        "Load from PDF file",
        "Skip this step",
    ])

    if source == "Skip this step":
        return []

    if source == "Load from PDF file":
        if not parse_pdf:
            print_error("PDF parsing is unavailable. Try pasting text instead.")
            return []
        path = prompt("Path to PDF file")
        if not path or not os.path.exists(path):
            print_error(f"File not found: {path}")
            return []
        print_info("Parsing PDF with Gemini…")
        events = parse_pdf(path)
    else:
        print("Paste your syllabus text below. When done, enter a line with just END:")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        text = "\n".join(lines)
        if not text.strip():
            print_warning("No text provided — skipping syllabus step.")
            return []
        print_info("Parsing syllabus with Gemini…")
        events = parse_syllabus(text)

    print_success(f"Found {len(events)} academic event(s).")
    display_events(events, "Academic Events")
    return events


def step_manual_events(mods):
    '''Allow the user to manually add events.'''
    Event = mods["Event"]
    rrule_reocurring = mods["rrule_reocurring"]

    if not Event:
        print_error("Event model unavailable.")
        return []

    print_section("Step 2 — Add Manual Events (optional)")
    if not confirm("Would you like to add events manually?"):
        return []

    manual_events = []
    while True:
        print_info("Adding a new event (leave title blank to finish):")
        title = prompt("  Event title")
        if not title:
            break

        date_str = prompt("  Date (YYYY-MM-DD)")
        start_str = prompt("  Start time (HH:MM, 24h)")
        end_str = prompt("  End time   (HH:MM, 24h)")
        description = prompt("  Description (optional)", default="")

        try:
            start = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
            end = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            print_error("Invalid date/time format — skipping this event.")
            continue

        rrule = None
        if rrule_reocurring and confirm("  Is this a recurring event?"):
            rrule = rrule_reocurring()

        event = Event(
            title=title,
            start_time=start,
            end_time=end,
            description=description or None,
            reoccuring=rrule,
        )
        manual_events.append(event)
        print_success(f"Added: {title}")

        if not confirm("Add another event?"):
            break

    print_success(f"Added {len(manual_events)} manual event(s).")
    return manual_events


def step_sports(mods):
    '''Fetch sports schedules and return a list of Events.'''
    SportScheduleFetcher = mods["SportScheduleFetcher"]
    LEAGUE_MAP = mods["LEAGUE_MAP"]

    if not SportScheduleFetcher:
        print_error("Sports schedule fetcher is unavailable (check dependencies).")
        return []

    print_section("Step 3 — Fetch Sports Schedule (optional)")
    if not confirm("Would you like to add a sports team schedule?"):
        return []

    fetcher = SportScheduleFetcher()
    all_sport_events = []

    while True:
        leagues = list(LEAGUE_MAP.keys())
        league = choose("Select a league:", leagues + ["Done — no more teams"])
        if league == "Done — no more teams":
            break

        if confirm(f"List all {league} teams?"):
            teams = fetcher.list_teams(league)
            if teams:
                print_info(f"{league} Teams:")
                for name in sorted(teams.keys()):
                    print(f"    {name}")

        team = prompt("Enter team name (or part of it)")
        if not team:
            continue

        print_info(f"Fetching {league} schedule for '{team}'…")
        events = fetcher.fetch_schedule(team, league)
        if events:
            print_success(f"Fetched {len(events)} game(s).")
            display_events(events, f"{team} Schedule")
            all_sport_events.extend(events)
        else:
            print_warning("No events returned.")

        if not confirm("Add another team?"):
            break

    return all_sport_events


def step_study_blocks(mods, all_events):
    '''Generate AI study blocks from combined events.'''
    generate_study_blocks = mods["generate_study_blocks"]

    if not generate_study_blocks:
        print_error("Study block generator is unavailable (check dependencies).")
        return []

    print_section("Step 4 — Generate Study Blocks")
    if not all_events:
        print_warning("No events loaded yet — study block generation skipped.")
        return []

    if not confirm("Generate AI-powered study blocks around your schedule?"):
        return []

    print_info("Sending events to Gemini to generate study blocks…")
    study_blocks = generate_study_blocks(all_events)
    print_success(f"Generated {len(study_blocks)} study block(s).")
    display_events(study_blocks, "Study Blocks")
    return study_blocks


def step_export(mods, all_events):
    '''Export events to Google Calendar or a local .ics file.'''
    sync_all = mods["sync_all"]

    print_section("Step 5 — Export Calendar")
    if not all_events:
        print_warning("No events to export.")
        return

    export_choice = choose("How would you like to export?", [
        "Push to Google Calendar",
        "Save as local .ics file",
        "Both",
        "Skip export",
    ])

    if export_choice == "Skip export":
        return

    # ── Local .ics ──
    if export_choice in ("Save as local .ics file", "Both"):
        filename = prompt("Output filename", default="smartcal.ics")
        if not filename.endswith(".ics"):
            filename += ".ics"
        _write_ics(all_events, filename)

    # -- Google Calendar --
    if export_choice in ("Push to Google Calendar", "Both"):
        if not sync_all:
            print_error("Google Calendar sync is unavailable (check dependencies).")
            return
        cal_name = prompt("Calendar name", default="SmartIcs")
        print_info(f"Pushing {len(all_events)} event(s) to Google Calendar as '{cal_name}'...")
        try:
            sync_all(all_events, calendar_name=cal_name)
        except Exception as e:
            print_error(f"Google Calendar sync failed: {e}")


def _write_ics(events, filename):
    '''Write events to a local iCalendar (.ics) file.'''
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//SmartCal//SmartIcs//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for e in events:
        lines.append(e.to_ical().strip())
    lines.append("END:VCALENDAR")

    with open(filename, "w") as f:
        f.write("\n".join(lines))
    print_success(f"Saved {len(events)} event(s) to '{filename}'.")


# ── Summary ───────────────────────────────────────────────────────────────────

def print_summary(syllabus_events, manual_events, sport_events, study_blocks):
    total = len(syllabus_events) + len(manual_events) + len(sport_events) + len(study_blocks)
    print_section("Summary")
    print(f"    Academic events (syllabus) : {len(syllabus_events)}")
    print(f"     Manual events              : {len(manual_events)}")
    print(f"    Sports games               : {len(sport_events)}")
    print(f"    Study blocks               : {len(study_blocks)}")
    print(f"  ─────────────────────────────────")
    print(f"    Total events               : {total}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print_banner()
    print_info(f"Today is {datetime.now().strftime('%A, %B %d, %Y')}")

    mods = _import_modules()

    # Step 1 — Syllabus
    syllabus_events = step_syllabus(mods)

    # Step 2 — Manual events
    manual_events = step_manual_events(mods)

    # Step 3 — Sports
    sport_events = step_sports(mods)

    # Combined pool for study-block generation
    combined = syllabus_events + manual_events + sport_events

    # Step 4 — Study blocks
    study_blocks = step_study_blocks(mods, combined)

    # Final combined list
    all_events = combined + study_blocks

    # Summary
    print_summary(syllabus_events, manual_events, sport_events, study_blocks)

    # Step 5 — Export
    step_export(mods, all_events)

    print("\n\033[36m  All done! Good luck this semester. \033[0m\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\033[33m  Cancelled. Goodbye!\033[0m\n")
        sys.exit(0)