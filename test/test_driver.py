from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os

from .utils import SubdueTestCase, TemporaryDirectory, OutStreamCheckedCapture
from . import utils
import subdue

class TestDriverMain(SubdueTestCase):


    def test_vanilla_driver(self):
        """
        Call the driver function directly with no arguments
        """
        with OutStreamCheckedCapture(self) as cap:
            subdue.sub.main([], exit=False)
        cap.stdout.contains("built-in command: help not yet implemented")

    def test_top_level_launch_thin(self):
        """
        Launch a top level subcommand with the library
        """
        with TemporaryDirectory(cd=True) as d:
            with OutStreamCheckedCapture(self):
                subdue.main(['subdue', 'new', '--thin', 'mysub'])

            sub_root = os.path.join(d, 'mysub')
            utils.create_subcommand(sub_root, 'mycommand', """\
                #!/bin/bash
                echo "This is foo"
                """)

            caller = utils.SubprocessCaller()
            with OutStreamCheckedCapture(self) as cap:
                subdue.sub.main(['mycommand'],
                                sub_path=sub_root,
                                command_runner=caller,
                                exit=False)
            self.assertIsNotNone(caller.returncode, "No command was called. {}".format(cap))
            self.assertEqual(caller.returncode, 0)
            cap.stdout.matches(r"^This is foo\n")


    def test_top_level_launch_fat(self):
        """
        Launch a top level subcommand with the driver
        """
        with TemporaryDirectory(cd=True) as d:

            with OutStreamCheckedCapture(self):
                subdue.main(['subdue', 'new', 'mysub'])

            sub_root = os.path.join(d, 'mysub')
            utils.create_subcommand(sub_root, 'mycommand', """\
                #!/bin/bash
                echo "This is foo"
                """)

            with OutStreamCheckedCapture(self) as cap:
                return_code = utils.call_driver_for(sub_root, ['mycommand'])

            self.assertEqual(return_code, 0, "Return code ({}) != expected ({}). Capture: {}".format(return_code, 0, cap))
            cap.stdout.matches(r"^This is foo\n")


class TestDriverOptions(SubdueTestCase):

    def _checkEval(self, sub_root, expected_rc, command):
        with OutStreamCheckedCapture(self) as cap:
            return_code = utils.call_driver_for(sub_root, ['--is-eval', command])

        self.assertEqual(return_code, expected_rc,
                "--is-eval returned {} for command {}, but expected {}. Capture: {}".format(
                    return_code, command, expected_rc, cap))
        cap.stdout.is_empty()

    def assertIsEval(self, sub_root, command):
        return self._checkEval(sub_root, 0, command)

    def assertIsNotEval(self, sub_root, command):
        return self._checkEval(sub_root, 1, command)

    def test_is_eval(self):
        subname = 'evalsub'
        with TemporaryDirectory(cd=True) as d:

            with OutStreamCheckedCapture(self):
                subdue.main(['subdue', 'new', subname])

            sub_root = os.path.join(d, subname)
            utils.create_subcommand(sub_root, 'sh-eval', """\
                #!/bin/bash
                echo "This is my eval command"
                """)
            utils.create_subcommand(sub_root, 'foobar', """\
                #!/bin/bash
                echo "This is my regular command"
                """)

            self.assertIsEval(sub_root, 'eval')
            self.assertIsNotEval(sub_root, 'sh-eval')
            self.assertIsNotEval(sub_root, 'foobar')
