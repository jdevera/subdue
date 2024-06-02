from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import json
import os
import stat
import textwrap

from .utils import SubdueTestCase, TempSub, TemporaryDirectory
from .import utils


SHOW_ENV_COMMAND='''
import os, json, sys

json.dump({ str(k):str(v) for k,v in os.environ.items() }, sys.stdout)
'''

SUB_ENV_VARS = sorted([
    '_SUB_NAME_',
    '_SUB_COMMAND_',
    '_SUB_PATH_COMMAND_',
    '_SUB_PATH_ROOT_',
    '_SUB_PATH_SHARED_',
    '_SUB_PATH_LIB_',
    '_SUB_IS_EVAL_',
    '_SUB_SHELL_'
    ])


class TestEnvironmentVariables(SubdueTestCase):

    def test_all_vars(self):
        env = None
        with TempSub(self, name='simple', thin=False) as s:
            out = s.create_subcommand('status', 'python', SHOW_ENV_COMMAND
                ).run_it(
                ).assertSucess(
                ).stdout
            env = json.loads(str(out.text))

        self.assertIsNotNone(env)
        self.assertIsInstance(env, dict)
        sub_vars = {k:v for k,v in env.items() if k.startswith('_SUB_')}

        self.assertEqual(SUB_ENV_VARS, sorted(sub_vars.keys()))
        self.assertEqual(s.name, sub_vars['_SUB_NAME_'])
        self.assertEqual('status', sub_vars['_SUB_COMMAND_'])
        self.assertEqual(s.sub_root, sub_vars['_SUB_PATH_ROOT_'])
        self.assertEqual(os.path.join(s.sub_root, 'commands', 'status'), sub_vars['_SUB_PATH_COMMAND_'])
        self.assertEqual(os.path.join(s.sub_root, 'shared'), sub_vars['_SUB_PATH_SHARED_'])
        self.assertEqual(os.path.join(s.sub_root, 'lib'), sub_vars['_SUB_PATH_LIB_'])
        self.assertEqual('0', sub_vars['_SUB_IS_EVAL_'])
        self.assertEqual('', sub_vars['_SUB_SHELL_'])

    def test_shell_arg(self):
        with TempSub(self, name='shellsub', thin=False) as s:
            s.create_subcommand('shellcommand', 'sh', 'echo SHELL:$_SUB_SHELL_')
            s.run('--shell', 'FOOBARSH', 'shellcommand'
                ).assertSucess(
                ).stdout.matches('SHELL:FOOBARSH')

    def test_eval_var(self):
        with TempSub(self, name='evalsub', thin=False) as s:
            s.create_subcommand('sh-evalme', 'sh', 'echo EVAL:$_SUB_IS_EVAL_')

            s.run('evalme'
                ).assertSucess(
                ).stdout.matches('EVAL:1')

            s.run('sh-evalme'
                ).assertSucess(
                ).stdout.matches('EVAL:0')

    def test_path(self):
        with TempSub(self, name='paths', thin=False) as s:
            out = s.create_subcommand('show', 'sh', 'echo "$PATH"'
                ).run_it(
                ).assertSucess(
                ).stdout.text
            paths = str(out).split(':')
            self.assertEqual(os.path.join(s.sub_root, 'bin'), paths.pop(0))
            self.assertEqual(os.path.join(s.sub_root, 'lib'), paths.pop(0))


class TestEnvironmentVariablesOnThinSub(SubdueTestCase):

    def test_all_vars(self):
        env = None
        with TempSub(self, name='simple', thin=True) as s:
            out = s.create_subcommand('status', 'python', SHOW_ENV_COMMAND
                ).run_it(
                ).assertSucess(
                ).stdout.text
            env = json.loads(str(out))

        self.assertIsNotNone(env)
        self.assertIsInstance(env, dict)
        sub_vars = {k:v for k,v in env.items() if k.startswith('_SUB_')}

        self.assertEqual(SUB_ENV_VARS, sorted(sub_vars.keys()))
        # The name might not be right for thin subs run from tests
        # self.assertEqual(s.name, sub_vars['_SUB_NAME_'])
        self.assertEqual('status', sub_vars['_SUB_COMMAND_'])
        self.assertEqual(s.sub_root, sub_vars['_SUB_PATH_ROOT_'])
        self.assertEqual(os.path.join(s.sub_root, 'commands', 'status'), sub_vars['_SUB_PATH_COMMAND_'])
        self.assertEqual(os.path.join(s.sub_root, 'shared'), sub_vars['_SUB_PATH_SHARED_'])
        self.assertEqual(os.path.join(s.sub_root, 'lib'), sub_vars['_SUB_PATH_LIB_'])
        self.assertEqual('0', sub_vars['_SUB_IS_EVAL_'])
        self.assertEqual('', sub_vars['_SUB_SHELL_'])


    def test_name_source(self):
        """
        Check that the sub name in the environment is set from the driver name,
        not from the root of the sub
        """

        # Create a thin sub
        with TempSub(self, name='thinname', thin=True) as s:
            s.create_subcommand('showname', 'sh', 'echo NAME:$_SUB_NAME_')

            # And a temporary driver for it
            with TemporaryDirectory() as driverdir:
                driver = os.path.join(driverdir, 'drivername')
                with open(driver, 'w') as fdrv:
                    fdrv.write(textwrap.dedent('''\
                        #!/usr/bin/env python
                        from subdue.sub import main
                        main(sub_path="{}")
                        '''.format(s.sub_root)))
                os.chmod(driver, os.stat(driver).st_mode | stat.S_IXUSR)

                # Run this driver
                with utils.OutStreamCheckedCapture(self) as cap:
                    return_code = utils.call_driver(driver, ['showname'])

                self.assertEqual(return_code, 0, "returned {} for showname, but expected 0. Capture: {}".format( return_code, cap))

                # The name in the environment should come from the driver, not the sub
                cap.stdout.matches('NAME:drivername')
