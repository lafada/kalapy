"""This module defines saveral utility functions to type cast values from
python to database and vice versa (most functions are adjopted from django).
"""

import datetime, decimal
from time import time


def date_to_python(value):
    return datetime.date(*map(int, value.split('-'))) if value else None

def time_to_python(value):
    if not value: 
        return None
    hour, minutes, seconds = value.split(':')
    if '.' in seconds: # check whether seconds have a fractional part
        seconds, microseconds = seconds.split('.')
    else:
        microseconds = '0'
    return datetime.time(int(hour), int(minutes), int(seconds), int(float('.'+microseconds) * 1000000))

def datetime_to_python(value):
    # "2005-07-29 15:48:00.590358-05"
    # "2005-07-29 09:56:00-05"
    if not value: return None
    if not ' ' in value: return date_to_python(value)
    d, t = value.split()
    # Extract timezone information, if it exists. Currently we just throw
    # it away, but in the future we may make use of it.
    if '-' in t:
        t, tz = t.split('-', 1)
        tz = '-' + tz
    elif '+' in t:
        t, tz = t.split('+', 1)
        tz = '+' + tz
    else:
        tz = ''
    dates = d.split('-')
    times = t.split(':')
    seconds = times[2]
    if '.' in seconds: # check whether seconds have a fractional part
        seconds, microseconds = seconds.split('.')
    else:
        microseconds = '0'
    return datetime.datetime(int(dates[0]), int(dates[1]), int(dates[2]),
        int(times[0]), int(times[1]), int(seconds), int(float('.'+microseconds) * 1000000))

def decimal_to_python(value):
    if value is None:
        return None
    return decimal.Decimal(value)

def decimal_to_database(value):
    if value is None:
        return None
    return str(value)

def str_to_database(value):
    return value.decode('utf-8')

