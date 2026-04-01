'''
Parses student syllabus input using the Gemini API.
Accepts raw text or a PDF file path, extracts academic deadlines and exam dates,
and returns them as a structured list of Event objects.
'''

import json
from google import genai
from datetime import datetime
import fitz
from models.event import Event
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def parse_syllabus(text):
    prompt = """
   Extract all deadlines and exams from this syllabus, including start times and end times.
    Return ONLY a JSON array with no extra text. Each item must have:
    - title: name of the event
    - date: in YYYY-MM-DD format
    - start_time: in HH:MM 24hr format if a time is mentioned, otherwise null
    - end_time: in HH:MM 24hr format if a time is mentioned, otherwise null
    - description: any extra details or empty string

    IMPORTANT: "3:30pm to 5:30pm" means start_time is 15:30 and end_time is 17:30. After 12:00pm, 1:00pm,2:00pm all the way to 11:00pm coorespond with 13:00pm, 14:00pm all the way to 23:00pm

    IMPORTANT: If the syllabus mentions a specific time for an event, you MUST extract it into start_time and end_time.
    """ + text

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    raw = response.text.strip()
    if "```" in raw:
        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")

    events = []
    try:
        items = json.loads(raw)
        for item in items:
            try:
                if not item.get("date") or item["date"] == "null" or item["date"] is None:
                    continue
                date = datetime.strptime(item["date"], "%Y-%m-%d")

                if item.get("start_time") and item["start_time"] != "null":
                    start = datetime.strptime(f"{item['date']} {item['start_time']}", "%Y-%m-%d %H:%M")
                else:
                    start = date.replace(hour=0, minute=0)

                if item.get("end_time") and item["end_time"] != "null":
                    end = datetime.strptime(f"{item['date']} {item['end_time']}", "%Y-%m-%d %H:%M")
                else:
                    end = date.replace(hour=23, minute=59)

                event = Event(title=item["title"], start_time=start, end_time=end, description=item.get("description", ""), source="syllabus_parser")
                events.append(event)
            except Exception as item_error:
                print(f"Skipping item due to error: {item_error} — item was: {item}")
                continue
    except Exception as e:
        return events
    return events

def parse_pdf(filepath):
    '''
    Accepts a PDF file path, extracts the text using PyMuPDF,
    and passes it to parse_syllabus(). Returns a list of Event objects.
    '''
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    return parse_syllabus(text)
