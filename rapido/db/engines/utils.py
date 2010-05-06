import datetime, decimal
from time import time


def date_to_py(value):
    return datetime.date(*map(int, value.split('-'))) if value else None

def time_to_py(value):
    return value

def datetime_to_py(value):
    return value

def decimal_to_py(value):
    if value is None:
        return None
    return decimal.Decimal(value)

def decimal_to_db(value):
    if value is None:
        return None
    return str(value)

def str_to_db(value):
    return value.decode('utf-8')

