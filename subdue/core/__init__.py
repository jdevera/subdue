__all__ = [
    'BANNER',
    'DEFAULT_DRIVER_CODE'
    'die',
    'verbose',
    'set_color_policy',
]

import sys as _sys
from . import color as _color

BANNER = """\
           _         _
 ___ _   _| |__   __| |_   _  ___
/ __| | | | '_ \ / _` | | | |/ _ \\
\__ \ |_| | |_) | (_| | |_| |  __/
|___/\__,_|_.__/ \__,_|\__,_|\___|
"""

DEFAULT_DRIVER_CODE = """\
#!/usr/bin/env python
from subdue.sub import main
main()
"""

verbose = False


def set_color_policy(policy):
    _color.color_policy = policy


def die(msg):
    _sys.stderr.write(msg)
    _sys.stderr.write("\n")
    _sys.stderr.flush()
    _sys.exit(1)

