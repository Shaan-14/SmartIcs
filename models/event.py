from datetime import datetime
'''
Core data model for the SmartCal application.
Defines the Event class used as a shared data contract across all services.
Stores event attributes and provides utility methods for conflict detection,
iCalendar formatting, serialization, and validation.
'''

class Event:
    '''
    Represents a calendar event with attributes like title, start time, end time,
    location, description, and source. Provides methods for conflict detection,
    iCalendar formatting, serialization, and validation.
    '''
    def __init__(self, title, start_time, end_time, description=None, reoccuring=None, location=None, source=None):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.reoccuring = reoccuring
        self.location = location
        self.source = source

    def conflicts_with(self, other_event):
        '''
        Determines if this event conflicts with another event based on overlapping times.
        '''
        return (self.start_time < other_event.end_time) and (self.end_time > other_event.start_time)

    def to_ical(self):
        '''
        Converts the event to an iCalendar VEVENT string representation.
        '''
        ical_event = f"BEGIN:VEVENT\nSUMMARY:{self.title}\nDTSTART:{self.start_time.strftime('%Y%m%dT%H%M%S')}\nDTEND:{self.end_time.strftime('%Y%m%dT%H%M%S')}\n"
        if self.description:
            ical_event += f"DESCRIPTION:{self.description}\n"
        if self.location:
            ical_event += f"LOCATION:{self.location}\n"
        if self.reoccuring:
            ical_event += f"RRULE:{self.reoccuring}\n"
        ical_event += "END:VEVENT\n"
        return ical_event

    def serialize(self):
        '''
        Serializes the event to a dictionary for JSON storage or transmission.
        '''
        return {
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'location': self.location,
            'description': self.description,
            'source': self.source
        }

    @staticmethod
    def deserialize(data):
        '''
        Deserializes a dictionary back into an Event object.
        '''
        return Event(
            title=data['title'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            location=data.get('location'),
            description=data.get('description'),
            source=data.get('source')
        )

    def is_valid(self):
        '''
        Validates the event data to ensure required fields are present and times are logical.
        '''
        if not self.title or not self.start_time or not self.end_time:
            return False
        return self.start_time < self.end_time