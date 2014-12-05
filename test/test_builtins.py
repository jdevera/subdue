from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals


from .utils import SubdueTestCase, TempSub


def lines(items):
    return '\n'.join(items.split()) + '\n'

class TestBuiltinCommands(SubdueTestCase):

    def test_commands(self):
        commands = [
                'dir1/cmd1.1',
                'dir1/cmd1.2',
                'dir1/cmd1.2',
                'dir1/dir1.1/cmd1.1.1',
                'dir1/dir1.1/cmd1.1.2',
                'dir1/dir1.1/cmd1.1.3',
                'cmd1',
                'sh-eval',
                'dir2/cmd2.1',
                'sh-absurd/contained',
                ]
        with TempSub(self, name='boo', thin=False) as s:
            for command in commands:
                s.create_subcommand(command, 'sh' '')

            s.run('commands').assertSucess(
                    ).stdout.matches(lines('cmd1 dir1 dir2 eval sh-absurd'), anchored=True)

            s.run('commands',  'dir1').assertSucess(
                    ).stdout.matches(lines('cmd1.1 cmd1.2 dir1.1'), anchored=True)

            s.run('commands',  'dir1', 'dir1.1').assertSucess(
                    ).stdout.matches(lines('cmd1.1.1 cmd1.1.2 cmd1.1.3'), anchored=True)

            s.run('commands',  'dir2').assertSucess(
                    ).stdout.matches(lines('cmd2.1'), anchored=True)

