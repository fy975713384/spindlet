from enum import Enum


class DatePart(Enum):
    year = "YEAR"
    quarter = "QUARTER"
    month = "MONTH"
    week = "WEEK"
    day = "DAY"
    hour = "HOUR"
    minute = "MINUTE"
    second = "SECOND"
    microsecond = "MICROSECOND"
