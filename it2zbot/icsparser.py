from datetime import datetime, timezone
from typing import TypedDict

import httpx


class VEvent(TypedDict):
    uid: str
    summary: str
    description: str
    class_: str
    last_modified: datetime
    location: str
    dtstamp: datetime
    dtstart: datetime
    dtend: datetime
    categories: str


class CalendarParser:
    def __init__(self, userid: str, authtoken: str):
        self.url = f"https://moodle.itech-bs14.de/calendar/export_execute.php?userid={userid}&authtoken={authtoken}&preset_what=all&preset_time=weeknow"
        self.events: list[VEvent] = []

    def get_events(self):
        with httpx.Client() as client:
            text = client.get(self.url).text
        current_event: VEvent = {}

        def split(line: str):
            return line.split(":", 1)[1].replace("\\n", "\n")

        def parse_date(date_string):
            return int(datetime.timestamp(datetime.strptime(date_string, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)))

        for line in text.split("\n"):
            line = line.rstrip()
            if line == "BEGIN:VEVENT":
                current_event: VEvent = {}
            if line == "END:VEVENT":
                self.events.append(current_event)
            if line.startswith("UID:"):
                current_event["uid"] = split(line)
            if line.startswith("SUMMARY:"):
                current_event["summary"] = split(line)
            if line.startswith("DESCRIPTION:"):
                current_event["description"] = split(line)
            if line.startswith("CLASS:"):
                current_event["class_"] = split(line)
            if line.startswith("LAST-MODIFIED:"):
                current_event["last_modified"] = parse_date(split(line))
            if line.startswith("LOCATION:"):
                current_event["location"] = split(line)
            if line.startswith("DTSTAMP:"):
                current_event["dtstamp"] = parse_date(split(line))
            if line.startswith("DTSTART:"):
                current_event["dtstart"] = parse_date(split(line))
            if line.startswith("DTEND:"):
                current_event["dtend"] = parse_date(split(line))
            if line.startswith("CATEGORIES:"):
                current_event["categories"] = split(line)
        return self.events
