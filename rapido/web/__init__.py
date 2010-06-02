
# Export some useful names from Werkzeug and Jinja2
from werkzeug import abort, redirect
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.contrib.securecookie import SecureCookie
from jinja2 import Markup, escape

from webapp import *

# remove module references to hide them from direct outside access
map(lambda n: globals().pop(n), ['webapp'])

