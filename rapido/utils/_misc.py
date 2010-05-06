
def to_unicode(value):
    """Convert the given value to Unicode string.
    """

    if isinstance(value, unicode):
        return value

    if hasattr(value, "__unicode__"):
        return unicode(value)

    try: # first try without encoding
        return unicode(value)
    except:
        pass

    try: # then try with utf-8
        return unicode(value, 'utf-8')
    except:
        pass

    try: # then try with extened iso-8858
        return unicode(value, 'iso-8859-15')
    except:
        pass

    try:
        return to_unicode(str(value))
    except:
        return " ".join([to_unicode(s) for s in value])

