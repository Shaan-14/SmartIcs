'''
Unit tests for the StudyBlockGenerator service.
Tests free slot identification, Gemini prompt construction,
and correct generation of study block Events around existing calendar events.
'''

from services.study_block_generator import generate_study_blocks
from models.event import Event
from datetime import datetime, timedelta

# Helper to print blocks nicely
def print_blocks(blocks):
    for b in blocks:
        start_str = b.start_time.strftime("%I:%M %p")
        end_str = b.end_time.strftime("%I:%M %p")
        print(f"  {b.title} | {b.start_time.date()} | {start_str} - {end_str}")
        if b.description:
            print(f"    → {b.description}")

# ─────────────────────────────────────────────
# Test 1: Exam in 7 days (should get 7 days of study blocks)
# ─────────────────────────────────────────────
print("=" * 50)
print("Test 1: Exam in 7 days")
print("=" * 50)

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
exam_date = today + timedelta(days=7)

events_test1 = [
    Event(
        title="Midterm Exam",
        start_time=exam_date.replace(hour=18, minute=30),
        end_time=exam_date.replace(hour=20, minute=0),
        description="Covers chapters 1-6",
        source="syllabus_parser"
    )
]

blocks = generate_study_blocks(events_test1)
print(f"Generated {len(blocks)} study blocks:")
print_blocks(blocks)

# ─────────────────────────────────────────────
# Test 2: Assignment due in 3 days
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("Test 2: Assignment due in 3 days")
print("=" * 50) 

due_date = today + timedelta(days=3)

events_test2 = [
    Event(
        title="Assignment 2",
        start_time=due_date.replace(hour=23, minute=59),
        end_time=due_date.replace(hour=23, minute=59),
        description="Submit to OWL",
        source="syllabus_parser"
    )
]

blocks = generate_study_blocks(events_test2)
print(f"Generated {len(blocks)} study blocks:")
print_blocks(blocks)

# ─────────────────────────────────────────────
# Test 3: Sports game conflicts with study time
# (game should be skipped if exam is critical)
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("Test 3: Sports game conflicts with exam study time")
print("=" * 50)

exam_date2 = today + timedelta(days=5)
game_date = today + timedelta(days=4)

events_test3 = [
    Event(
        title="Final Exam",
        start_time=exam_date2.replace(hour=9, minute=0),
        end_time=exam_date2.replace(hour=11, minute=0),
        description="Cumulative final",
        source="syllabus_parser"
    ),
    Event(
        title="Toronto Raptors vs Boston Celtics",
        start_time=game_date.replace(hour=19, minute=0),
        end_time=game_date.replace(hour=21, minute=30),
        description="NBA Game",
        source="sport_schedule_fetcher"
    )
]

blocks = generate_study_blocks(events_test3)
print(f"Generated {len(blocks)} study blocks:")
print_blocks(blocks)

# ─────────────────────────────────────────────
# Test 4: Multiple events at once
# (quiz + assignment + game all in same week)
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("Test 4: Quiz + Assignment + Game in same week")
print("=" * 50)

quiz_date = today + timedelta(days=3)
assignment_date = today + timedelta(days=5)
game_date2 = today + timedelta(days=2)

events_test4 = [
    Event(
        title="Quiz 3",
        start_time=quiz_date.replace(hour=14, minute=0),
        end_time=quiz_date.replace(hour=14, minute=30),
        description="Chapter 7-9",
        source="syllabus_parser"
    ),
    Event(
        title="Assignment 3",
        start_time=assignment_date.replace(hour=23, minute=59),
        end_time=assignment_date.replace(hour=23, minute=59),
        description="Submit to OWL",
        source="syllabus_parser"
    ),
    Event(
        title="Toronto Maple Leafs vs Montreal Canadiens",
        start_time=game_date2.replace(hour=19, minute=30),
        end_time=game_date2.replace(hour=22, minute=0),
        description="NHL Game",
        source="sport_schedule_fetcher"
    )
]

blocks = generate_study_blocks(events_test4)
print(f"Generated {len(blocks)} study blocks:")
print_blocks(blocks)

