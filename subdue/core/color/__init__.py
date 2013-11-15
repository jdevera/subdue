import sys as _sys
from .ansi import Fore as _Fore, Style as _Style

_color_policy = 'default'

_module = _sys.modules[__name__]


def _using_colors():
    return (_color_policy == 'default' and _sys.stdout.isatty()
           ) or _color_policy == 'yes'


def _gen_col(ansi, name, is_bright=False):
    name = name if not is_bright else 'bright_' + name

    def f(s):
        """
        Template for colored text output
        """
        if not _using_colors():
            return s
        code = ansi
        if bright:
            code += _Style.BRIGHT
        return code + s + _Style.RESET_ALL

    f.__name__ = name
    setattr(_module, name, f)

# Programmatically add a series of functions to this module based on
# foreground colors
for _c in dir(_Fore):
    if not _c.startswith('_') and not _c == 'RESET':
        _name = _c.lower()
        _gen_col(getattr(_Fore, _c), name=_name, is_bright=False)
        _gen_col(getattr(_Fore, _c), name=_name, is_bright=True)


def bright(s):
    if not _using_colors():
        return s
    return _Style.BRIGHT + s + _Style.RESET_ALL


