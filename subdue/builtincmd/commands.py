from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from . import base
import os

@base.built_in_command('commands')
class Commands(base.BuiltInCommand):

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

