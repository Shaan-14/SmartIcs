'''
Unit tests for the Event model.
Tests attribute assignment, conflict detection via conflicts_with(),
iCalendar formatting, and input validation.
'''
from models.event import Event
import datetime

def test_event_creation():
    print("\n--- Event Creation ---")

    # Basic event
    e1 = Event(
        title="Lecture",
        start_time=datetime.datetime(2024, 6, 1, 10, 0),
        end_time=datetime.datetime(2024, 6, 1, 11, 0),
        description="Monday lecture"
    )
    print(f"[OK] Basic event created: '{e1.title}' {e1.start_time.strftime('%H:%M')} -> {e1.end_time.strftime('%H:%M')}")

    # No optional fields
    e2 = Event(
        title="Minimal Event",
        start_time=datetime.datetime(2024, 6, 1, 12, 0),
        end_time=datetime.datetime(2024, 6, 1, 13, 0)
    )
    print(f"[OK] Minimal event (no description): '{e2.title}', description={e2.description}, reoccuring={e2.reoccuring}")

    # Recurring event
    e3 = Event(
        title="Weekly Lab",
        start_time=datetime.datetime(2024, 6, 1, 14, 0),
        end_time=datetime.datetime(2024, 6, 1, 16, 0),
        reoccuring="FREQ=WEEKLY;COUNT=12"
    )
    print(f"[OK] Recurring event: '{e3.title}', rule={e3.reoccuring}")

    # Multi-day event
    e4 = Event(
        title="Conference",
        start_time=datetime.datetime(2024, 6, 1, 9, 0),
        end_time=datetime.datetime(2024, 6, 3, 17, 0)
    )
    duration = e4.end_time - e4.start_time
    print(f"[OK] Multi-day event: '{e4.title}', duration={duration.days} days")

    # Midnight crossing
    e5 = Event(
        title="Late Night Study",
        start_time=datetime.datetime(2024, 6, 1, 23, 0),
        end_time=datetime.datetime(2024, 6, 2, 1, 0)
    )
    print(f"[OK] Midnight crossing: '{e5.title}' {e5.start_time.strftime('%H:%M')} -> {e5.end_time.strftime('%H:%M')}")


def test_conflicts_with():
    print("\n--- Conflict Detection ---")

    base = Event("Base", datetime.datetime(2024, 6, 1, 10, 0), datetime.datetime(2024, 6, 1, 11, 0))

    cases = [
        ("Identical times",       datetime.datetime(2024, 6, 1, 10, 0),  datetime.datetime(2024, 6, 1, 11, 0),  True),
        ("Partial overlap start", datetime.datetime(2024, 6, 1, 10, 30), datetime.datetime(2024, 6, 1, 11, 30), True),
        ("Partial overlap end",   datetime.datetime(2024, 6, 1, 9, 30),  datetime.datetime(2024, 6, 1, 10, 30), True),
        ("Other contains base",   datetime.datetime(2024, 6, 1, 9, 0),   datetime.datetime(2024, 6, 1, 12, 0),  True),
        ("Base contains other",   datetime.datetime(2024, 6, 1, 10, 15), datetime.datetime(2024, 6, 1, 10, 45), True),
        ("1-minute overlap",      datetime.datetime(2024, 6, 1, 10, 59), datetime.datetime(2024, 6, 1, 11, 30), True),
        ("Back to back after",    datetime.datetime(2024, 6, 1, 11, 0),  datetime.datetime(2024, 6, 1, 12, 0),  False),
        ("Back to back before",   datetime.datetime(2024, 6, 1, 9, 0),   datetime.datetime(2024, 6, 1, 10, 0),  False),
        ("Completely before",     datetime.datetime(2024, 6, 1, 7, 0),   datetime.datetime(2024, 6, 1, 8, 0),   False),
        ("Completely after",      datetime.datetime(2024, 6, 1, 13, 0),  datetime.datetime(2024, 6, 1, 14, 0),  False),
        ("Different day",         datetime.datetime(2024, 6, 2, 10, 0),  datetime.datetime(2024, 6, 2, 11, 0),  False),
    ]

    all_passed = True
    for label, start, end, expected in cases:
        other = Event(label, start, end)
        result = base.conflicts_with(other)
        status = "OK" if result == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"[{status}] {label}: got={'CONFLICT' if result else 'NO CONFLICT'}, expected={'CONFLICT' if expected else 'NO CONFLICT'}")

    # Symmetry check
    other = Event("Overlap", datetime.datetime(2024, 6, 1, 10, 30), datetime.datetime(2024, 6, 1, 11, 30))
    forward = base.conflicts_with(other)
    reverse = other.conflicts_with(base)
    sym_status = "OK" if forward == reverse else "FAIL"
    print(f"[{sym_status}] Symmetry: base->other={forward}, other->base={reverse}")

    if all_passed:
        print("[OK] All conflict cases passed")


def test_to_ical():
    print("\n--- iCal Formatting ---")

    # Basic output
    e = Event("Lecture", datetime.datetime(2024, 6, 1, 10, 0), datetime.datetime(2024, 6, 1, 11, 0))
    output = e.to_ical()
    checks = ["BEGIN:VEVENT", "END:VEVENT", "SUMMARY:Lecture", "DTSTART:20240601T100000", "DTEND:20240601T110000"]
    for check in checks:
        status = "OK" if check in output else "FAIL"
        print(f"[{status}] Contains '{check}'")

    # With description
    e2 = Event("Exam", datetime.datetime(2024, 6, 1, 9, 0), datetime.datetime(2024, 6, 1, 11, 0),
               description="Final exam worth 40%")
    out2 = e2.to_ical()
    status = "OK" if "DESCRIPTION:Final exam worth 40%" in out2 else "FAIL"
    print(f"[{status}] Description included in ical")

    # With recurrence
    e3 = Event("Weekly Lab", datetime.datetime(2024, 6, 1, 14, 0), datetime.datetime(2024, 6, 1, 16, 0),
               reoccuring="FREQ=WEEKLY;COUNT=12")
    out3 = e3.to_ical()
    print(out3)
    status = "OK" if "RRULE:FREQ=WEEKLY;COUNT=12" in out3 else "FAIL"
    print(f"[{status}] Recurrence rule included in ical")

    # No optional fields — should NOT contain DESCRIPTION or RRULE
    e4 = Event("Minimal", datetime.datetime(2024, 6, 1, 10, 0), datetime.datetime(2024, 6, 1, 11, 0))
    out4 = e4.to_ical()
    status = "OK" if "DESCRIPTION" not in out4 and "RRULE" not in out4 else "FAIL"
    print(f"[{status}] Optional fields absent when not set")


def test_is_valid():
    print("\n--- Validation ---")

    cases = [
        ("Valid event",      "Lecture", datetime.datetime(2024, 6, 1, 10, 0), datetime.datetime(2024, 6, 1, 11, 0), True),
        ("Empty title",      "",        datetime.datetime(2024, 6, 1, 10, 0), datetime.datetime(2024, 6, 1, 11, 0), False),
        ("None title",       None,      datetime.datetime(2024, 6, 1, 10, 0), datetime.datetime(2024, 6, 1, 11, 0), False),
        ("None start_time",  "Event",   None,                                  datetime.datetime(2024, 6, 1, 11, 0), False),
        ("None end_time",    "Event",   datetime.datetime(2024, 6, 1, 10, 0), None,                                  False),
    ]

    for label, title, start, end, expected in cases:
        e = Event(title=title, start_time=start, end_time=end)
        result = e.is_valid()
        status = "OK" if result == expected else "FAIL"
        print(f"[{status}] {label}: got={result}, expected={expected}")


if __name__ == "__main__":
    test_event_creation()
    test_conflicts_with()
    test_to_ical()
    test_is_valid()
    print("\n--- Done ---")
    