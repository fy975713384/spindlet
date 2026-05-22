from pypika import Field
from pypika.functions import *


class DateFormat(Function):
    """ MySQL DATE_FORMAT 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_date-format
    """

    def __init__(self, field: str | Field | Function, fm: str = "%Y-%m-%d %H:%i:%S", alias=None):
        if isinstance(field, Field) and not alias:
            alias = field.name
        super(DateFormat, self).__init__("DATE_FORMAT", field, fm, alias=alias)


class DateAdd(Function):
    """ MySQL DATE_ADD 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_date-add
    """

    def __init__(self, date, interval):
        super(DateAdd, self).__init__("DATE_ADD", date, interval)


class DateSub(Function):
    """ MySQL DATE_SUB 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_date-sub
    """

    def __init__(self, date, interval):
        super(DateSub, self).__init__("DATE_SUB", date, interval)


class DateDiff(Function):
    """ MySQL DATEDIFF 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_datediff
    """

    def __init__(self, end_date, start_date):
        super(DateDiff, self).__init__("DATEDIFF", end_date, start_date)


class If(Function):
    """ MySQL IF 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/flow-control-functions.html#function_if
    """

    def __init__(self, expr1, expr2, expr3):
        super(If, self).__init__("IF", expr1, expr2, expr3)


class Rand(Function):
    """ MySQL RAND 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/mathematical-functions.html#function_rand
    """

    def __init__(self, n: int = None):
        if isinstance(n, int):
            super(Rand, self).__init__("RAND", n)
        else:
            super(Rand, self).__init__("RAND")


class Year(Function):
    """ MySQL YEAR 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_year
    """

    def __init__(self, term, alias=None):
        super(Year, self).__init__("YEAR", term, alias=alias)


class YearWeek(Function):
    """ MySQL YEARWEEK 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_yearweek
    """

    def __init__(self, term, mode=1, alias=None):
        super(YearWeek, self).__init__("YEARWEEK", term, mode, alias=alias)


class Month(Function):
    """ MySQL MONTH 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_month
    """

    def __init__(self, term, alias=None):
        super(Month, self).__init__("MONTH", term, alias=alias)


class Day(Function):
    """ MySQL DAY 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_day
    """

    def __init__(self, term, alias=None):
        super(Day, self).__init__("DAY", term, alias=alias)


class Week(Function):
    """ MySQL WEEK 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_week
    """

    def __init__(self, term, mode=1, alias=None):
        super(Week, self).__init__("WEEK", term, mode, alias=alias)


class WeekDay(Function):
    """ MySQL WEEKDAY 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_weekday
    """

    def __init__(self, term, alias=None):
        super(WeekDay, self).__init__("WEEKDAY", term, alias=alias)


class WeekOfYear(Function):
    """ MySQL WEEKOFYEAR 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_weekofyear
    """

    def __init__(self, term, alias=None):
        super(WeekOfYear, self).__init__("WEEKOFYEAR", term, alias=alias)


class UnixTimestamp(Function):
    """ MySQL UNIX_TIMESTAMP 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/date-and-time-functions.html#function_unix-timestamp
    """

    def __init__(self, term, alias=None):
        super(UnixTimestamp, self).__init__("UNIX_TIMESTAMP", term, alias=alias)


class GroupConcat(Function):
    """ MySQL GROUP_CONCAT 函数
    see: https://dev.mysql.com/doc/refman/8.0/en/aggregate-functions.html#function_group-concat
    """

    def __init__(self, term, alias=None):
        super(GroupConcat, self).__init__("GROUP_CONCAT", term, alias=alias)
