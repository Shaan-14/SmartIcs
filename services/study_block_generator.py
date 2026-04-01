'''
Generates AI-powered study blocks using the Gemini API.
Takes existing events and deadlines, identifies free time slots, and prompts
Gemini to schedule study sessions that avoid conflicts and prioritize by weight.
'''
import json
from google import genai
from datetime import datetime
from models.event import Event
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_study_blocks(events):
    '''
    Takes a list of Event objects (syllabus deadlines + sports games) and 
    generates study blocks around them.
    Returns a list of Event objects representing study sessions.
    '''

    # Separate academic events from sports games
    academic_events = []
    sports_events = []

    for e in events:
        title_lower = e.title.lower()
        if any(word in title_lower for word in ["game", "vs", "nhl", "nba", "mlb", "nfl", "sport",
                                                 "blue jays", "leafs", "raptors", "jays"]):
            sports_events.append(e)
        else:
            academic_events.append(e)

    # Serialize all events to pass to Gemini
    event_list = []
    for e in events:
        event_list.append({
            "title": e.title,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "description": e.description or "",
            "type": "sports" if e in sports_events else "academic"
        })

    prompt = f"""
You are a smart student scheduling assistant. Below is a list of a student's upcoming events
including academic deadlines, exams, and sports games.

Your job is to generate study blocks following these STRICT rules:

EXAMS, TESTS, QUIZZES, FINALS, MIDTERMS:
For each exam, you MUST generate ALL of the following blocks — do not skip any:
  - Day 7 through Day 3 before the exam: one 2-3 hour study block per day (5 blocks total)
  - Day 2 before the exam: one 5-6 hour INTENSIVE study block (REQUIRED, do not skip)
  - Day 1 before the exam: one 5-6 hour INTENSIVE study block (REQUIRED, do not skip)
  - Exam day morning: one 1-hour review block at 08:00-09:00 (REQUIRED, labelled "Review for [Exam Name]")

Example: if an exam is on June 4, you must produce blocks on May 28, 29, 30, 31, June 1 (2-3hr each),
June 2 (5-6hr intensive), June 3 (5-6hr intensive), and June 4 morning review. That is 8 blocks per exam.

ASSIGNMENTS:
- Schedule a 1-2 hour work block on each of the 2 days before the due date.
- Schedule a 2 hour block on the due date itself.

SPORTS GAMES:
- Schedule study blocks AROUND sports games whenever possible.
- A study block "conflicts" with a game ONLY if their time ranges actually overlap on the clock.
  A 09:00-11:00 study block does NOT conflict with a 19:00 game. They are on the same day but
  at completely different times. Only set conflicts_with_game to true if start/end times overlap.
- If a study block truly cannot avoid overlapping a game's actual start/end time, set
  conflicts_with_game to true and add to description: "Note: Conflicts with [game name] - studying takes priority."
- Never skip a required study block just because of a sports game.

GENERAL RULES:
- Avoid scheduling study blocks past midnight or before 07:00.
- If two study blocks fall on the same day, space them with at least a 1 hour break.
- Label each block clearly e.g. "Study for Test 1 - Day 5", "Study for Final Exam - Day 2 (Intensive)".
- The morning review on exam day must be labelled "Review for [Exam Name]".

Here are the existing events (includes both academic and sports):
{json.dumps(event_list, indent=2)}

Today's date is: {datetime.now().strftime("%Y-%m-%d")}

Return ONLY a JSON array with no extra text. Each study block must have:
- title: descriptive name
- date: in YYYY-MM-DD format
- start_time: in HH:MM 24hr format
- end_time: in HH:MM 24hr format
- description: brief note on what to focus on
- conflicts_with_game: true ONLY if the study block time range overlaps the game time range, otherwise false
- is_exam_day_review: true if this is the morning review block on the exam day itself, false otherwise
"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    raw = response.text.strip()
    if "```" in raw:
        raw = raw.replace("```json", "").replace("```", "")

    # Track exam events so we can enforce required blocks afterward
    exam_events = [e for e in academic_events if any(
        w in e.title.lower() for w in ["exam", "test", "quiz", "final", "midterm"]
    )]

    study_blocks = []
    try:
        items = json.loads(raw)
        for item in items:
            start = datetime.strptime(f"{item['date']} {item['start_time']}", "%Y-%m-%d %H:%M")
            end = datetime.strptime(f"{item['date']} {item['end_time']}", "%Y-%m-%d %H:%M")
            is_exam_day_review = item.get("is_exam_day_review", False)

            block = Event(
                title=item["title"],
                start_time=start,
                end_time=end,
                description=item.get("description", ""),
                source="study_block_generator"
            )

            # Check for conflicts with academic events (never allowed)
            # EXCEPTION: exam-day morning review blocks are always kept even if the
            # exam event spans all day (00:00-23:59), since the review happens before the exam.
            academic_conflict = False
            if not is_exam_day_review:
                for e in academic_events:
                    # Only count as a conflict if the academic event has a known,
                    # specific time (not an all-day placeholder spanning 00:00-23:59)
                    event_is_all_day = (
                        e.start_time.hour == 0 and e.start_time.minute == 0 and
                        e.end_time.hour == 23 and e.end_time.minute >= 59
                    )
                    if not event_is_all_day and block.conflicts_with(e):
                        academic_conflict = True
                        print(f"Skipped block (academic conflict): {block.title} on {item['date']}")
                        break

            if academic_conflict:
                continue

            # Only flag sports conflict if times genuinely overlap
            game_conflict = item.get("conflicts_with_game", False)
            if game_conflict:
                print(f"Note: '{block.title}' on {item['date']} overlaps a sports game - studying takes priority.")

            study_blocks.append(block)

    except Exception as e:
        print("Error parsing study blocks:", e)

    # ── Safety net: ensure every exam has its Day 2, Day 1, and morning review ──
    from datetime import timedelta
    generated_dates = {(b.title, b.start_time.date()) for b in study_blocks}

    for exam in exam_events:
        exam_date = exam.start_time.date()
        exam_name = exam.title

        # Day 2 intensive (2 days before)
        day2_date = exam_date - timedelta(days=2)
        day2_title = f"Study for {exam_name} - Day 2 (Intensive)"
        if not any(b.start_time.date() == day2_date and exam_name in b.title and "day 2" in b.title.lower() for b in study_blocks):
            block = Event(
                title=day2_title,
                start_time=datetime(day2_date.year, day2_date.month, day2_date.day, 9, 0),
                end_time=datetime(day2_date.year, day2_date.month, day2_date.day, 15, 0),
                description=f"Intensive 6-hour study session for {exam_name}.",
                source="study_block_generator"
            )
            study_blocks.append(block)
            print(f"[Safety net] Added missing: {day2_title}")

        # Day 1 intensive (1 day before)
        day1_date = exam_date - timedelta(days=1)
        day1_title = f"Study for {exam_name} - Day 1 (Intensive)"
        if not any(b.start_time.date() == day1_date and exam_name in b.title and "day 1" in b.title.lower() for b in study_blocks):
            block = Event(
                title=day1_title,
                start_time=datetime(day1_date.year, day1_date.month, day1_date.day, 9, 0),
                end_time=datetime(day1_date.year, day1_date.month, day1_date.day, 15, 0),
                description=f"Intensive 6-hour study session for {exam_name}.",
                source="study_block_generator"
            )
            study_blocks.append(block)
            print(f"[Safety net] Added missing: {day1_title}")

        # Morning review on exam day
        review_title = f"Review for {exam_name}"
        if not any(b.start_time.date() == exam_date and "review" in b.title.lower() and exam_name in b.title for b in study_blocks):
            block = Event(
                title=review_title,
                start_time=datetime(exam_date.year, exam_date.month, exam_date.day, 8, 0),
                end_time=datetime(exam_date.year, exam_date.month, exam_date.day, 9, 0),
                description=f"Final 1-hour review before {exam_name}.",
                source="study_block_generator"
            )
            study_blocks.append(block)
            print(f"[Safety net] Added missing: {review_title}")

    study_blocks.sort(key=lambda b: b.start_time)
    return study_blocks