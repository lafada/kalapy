from webapp import *

# remove module references to hide them from direct outside access
map(lambda n: globals().pop(n), ['webapp'])
