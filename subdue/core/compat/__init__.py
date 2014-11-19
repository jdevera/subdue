# -*- coding: utf-8 -*-

from .six import *

if PY3:
    import builtins as _builtins
    unicode = _builtins.str
else:
    import __builtin__ as _builtins
    unicode = _builtins.unicode

class UnicodeMixin(object):
    """
    Mixin class to handle defining the proper __str__/__unicode__ methods in
    Python 2 or 3.
    """

    if PY3: # Python 3
        def __str__(self):
            return self.__unicode__()
    else:  # Python 2
        def __str__(self):
            return self.__unicode__().encode('utf8')

