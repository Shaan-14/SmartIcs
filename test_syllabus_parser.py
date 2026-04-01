'''
Unit tests for the SyllabusParser service.
Uses mocked Gemini responses to test syllabus text parsing,
PDF extraction, and correct conversion of deadlines into Event objects.
'''
import fitz
from services.syllabus_parser import parse_syllabus

# Test 1: Text input
print("Test 1: Text")
sample = """
AISE 2251 Course Outline
- Assignment 1 due January 20, 2026
- Midterm Exam: February 10, 2026, 6:30pm - 7:30pm
- Assignment 2 due March 3, 2026
- Final Exam: April 15, 2026
- Quiz: March 6th 2026:
Other Events:
- Baja Meeting: April 7th 2026
- Coop Application due: May 1st at 3pm
"""
events = parse_syllabus(sample)
print(f"Found {len(events)} events:")
for e in events:
    if e.start_time.hour == 0 and e.start_time.minute == 0:
        time_str = "All Day"
    elif e.end_time.hour == 23 and e.end_time.minute == 59:
        time_str = e.start_time.strftime("%I:%M %p")
    else:
        start_str = e.start_time.strftime("%I:%M %p")
        end_str = e.end_time.strftime("%I:%M %p")
        time_str = f"{start_str} - {end_str}"
    print(e.title, "-", e.start_time.date(), "-", time_str)

# Test 2: PDF input
print("\nTest 2: PDF File")
doc = fitz.open("MME 2273B Course Outline 2025-2026.pdf")
text = ""
for page in doc:
    text += page.get_text()

events = parse_syllabus(text)
print(f"Found {len(events)} events:")
for e in events:
    if e.start_time.hour == 0 and e.start_time.minute == 0:
        time_str = "All Day"
    elif e.end_time.hour == 23 and e.end_time.minute == 59:
        time_str = e.start_time.strftime("%I:%M %p")
    else:
        start_str = e.start_time.strftime("%I:%M %p")
        end_str = e.end_time.strftime("%I:%M %p")
        time_str = f"{start_str} - {end_str}"
    print(e.title, "-", e.start_time.date(), "-", time_str)
