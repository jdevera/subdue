from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from .utils import SubdueTestCase, TempSub

class TestCommandExecution(SubdueTestCase):

    def test_simple_command(self):
        with TempSub(self, name='simple', thin=False) as s:
            s.create_subcommand('status', 'sh', '''echo "I am status"'''
                ).run_it(
                ).assertSucess(
                ).stdout.matches(r'^I am status$')

    def test_two_level_command(self):
        with TempSub(self, name='ex', thin=False) as sub:
            sub.create_subcommand('server/status', 'sh', '''echo "I am server status"'''
                ).run_it(
                ).assertSucess(
                ).stdout.matches(r'^I am server status$')

    def test_arguments(self):
        with TempSub(self, name='ex', thin=False) as sub:
            sub.create_subcommand('example/arguments', 'sh', '''echo "My arguments: $@"'''
                ).run_it('foo', 'bar', '-a', 'baz'
                ).assertSucess(
                ).stdout.matches(r'^My arguments: foo bar -a baz')
