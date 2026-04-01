'''
Utility module for formatting Event objects into iCalendar (.ics) structure.
Wraps the icalendar Python library and is used by CalendarManager
before writing events to a file or the Google Calendar API.
'''

class ICalFormatter:
    def __init__(self, calendar_name, events):
        self.calendar_name = calendar_name
        self.events = events
        with open(f"{self.calendar_name}.ics", "w") as f:
            f.write(self.to_ical())
    def to_ical(self):
        '''
        Converts the list of Event objects into a complete iCalendar string.
        '''
        ical_content = "BEGIN:VCALENDAR\nVERSION:2.0\n"
        for event in self.events:
            ical_content += event.to_ical()
        ical_content += "END:VCALENDAR"
        return ical_content
    def add_event(self, event):
        '''
        Adds a new Event to the calendar and updates the .ics file.
        '''
        self.events.append(event)
        with open(f"{self.calendar_name}.ics", "w") as f:
            f.write(self.to_ical())
    def remove_event(self, event):
        '''
        Removes an Event from the calendar and updates the .ics file.
        '''
        self.events = [e for e in self.events if e != event]
        with open(f"{self.calendar_name}.ics", "w") as f:
            f.write(self.to_ical())
    