# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os

registry = {}

def built_in_command(name):
    def wrapper(c):
        registry[name] = c
        c.name = name
        return c
    return wrapper


class _BuiltInCommand(object):
    name = None

    def __init__(self, args, paths):
        self.args = args
        self.paths = paths

    def __call__(self):
        print ("built-in command: {} not yet implemented".format(self.name))


@built_in_command('commands')
class Commands(_BuiltInCommand):

    def __init__(self, args, paths):
        super(Commands, self).__init__(args, paths)

    def __call__(self):
        path = os.path.join(self.paths.commands, *self.args[1:])
        if os.path.isdir(path):
            commands = self.get_container_commands(path)
            for command in commands:
                print(command)
            return 0
        return 1

    def get_container_commands(self, path):
        commands = []
        for path, dirs, files in os.walk(path):
            commands += dirs
            for f in files:
                if os.access(os.path.join(path, f), os.X_OK):
                    if f.startswith('sh-'):
                        f = f[3:]
                    commands.append(f)
            break
        return sorted(commands)


@built_in_command('help')
class Help(_BuiltInCommand):
    def __init__(self, args, paths):
        super(Help, self).__init__(args, paths)
