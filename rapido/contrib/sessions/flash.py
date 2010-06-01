from rapido.web import request


def flash(message, category='message'):
    """Flashes a message to the next request. The flashed messages will
    be stored in session and will be removed from session when consumed
    by accessing `request.flashes`, though the flashes will be available
    throught the request.

    :param message: message to be flashed
    :param category: message category, like `message`, `error`, `info`.
    """
    request.session.setdefault('_flashes', []).append((category, message))


def flashes():
    """Access all the flashed messages and remove them from the session.
    The messages will be available throught the request though.

    Example:

    .. sourcecode:: html+jinja

        {% for category, message in request.flashes() %}
            <div class="flash-{{ category }}">{{ message }}</div>
        {% endfor %}

    """
    flashes = getattr(request, '_flashes', None)
    if flashes is None:
        request._flashes = flashes = request.session.pop('_flashes', [])
    return flashes

