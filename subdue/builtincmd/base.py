from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

registry = {}

def built_in_command(name):
    def wrapper(c):
        registry[name] = c
        c.name = name
        return c
    return wrapper

class BuiltInCommand(object):
    name = None

    def __init__(self, args, paths):
        self.args = args
        self.paths = paths

    def __call__(self):
        print ("built-in command: {} not yet implemented".format(self.name))
