import requests
from icalendar import Calendar, Event
from collections import defaultdict
from datetime import datetime, timedelta
import pytz
import os

# Config
ICS_URL = os.getenv('ICS_URL', 'https://example.com/path/to/calendar.ics')
LOCAL_TZ = pytz.timezone('Europe/London')

# Download ICS file
response = requests.get(ICS_URL)
response.raise_for_status()
cal = Calendar.from_ical(response.content)

# Group events by shift day
events_by_day = defaultdict(list)

for component in cal.walk('VEVENT'):
    if not isinstance(component, Event):
        continue

    start = component.get('dtstart').dt
    end = component.get('dtend').dt
    summary = str(component.get('summary')).strip()

    # Ensure timezone-aware datetimes
    if isinstance(start, datetime) and start.tzinfo is None:
        start = LOCAL_TZ.localize(start)
    if isinstance(end, datetime) and end.tzinfo is None:
        end = LOCAL_TZ.localize(end)

    # Anchor date back 6 hours to group overnight shifts together
    shift_anchor = (start - timedelta(hours=6)).date()
    events_by_day[shift_anchor].append((start, end, summary))

# Create new calendar
new_cal = Calendar()
new_cal.add('prodid', '-//Merged Work Calendar//')
new_cal.add('version', '2.0')

for shift_day, events in sorted(events_by_day.items()):
    starts = [e[0] for e in events]
    ends = [e[1] for e in events]

    merged_event = Event()
    merged_event.add('summary', "Work")
    merged_event.add('dtstart', min(starts))
    merged_event.add('dtend', max(ends))
    new_cal.add_component(merged_event)

os.makedirs('output', exist_ok=True)
with open('output/merged.ics', 'wb') as f:
    f.write(new_cal.to_ical())
