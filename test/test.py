from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import os
import subdue
import subdue.core
import subdue.sub
from .utils import SubdueTestCase, TemporaryDirectory, OutStreamCheckedCapture
from . import utils

class TestMain(SubdueTestCase):


    def test_noargs(self):
        """
        Verify that subdue exists with error if no arguments are provided
        """
        sys.argv = ['subdue']

        with OutStreamCheckedCapture(self) as cap:
            self.assertRaises(SystemExit, subdue.main)
        cap.stderr.matches(r'subdue: error: too few arguments'
        ).matches(r'\busage\b')

    def test_badnames(self):
        """
        Verify correct errors are reported due to invalid sub names
        """
        def new_bad(name):
            with OutStreamCheckedCapture(self) as cap:
                with self.assertRaises(SystemExit):
                    subdue.main(['subdue', 'new', '--', name])
            return cap.stderr

        sys.argv = ['subdue']

        new_bad(' bad'
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(    ' - Starts with spaces\n'
                 ).contains('\n - ', times=1
                 )
        new_bad('bad '
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(    ' - Ends with spaces\n'
                 ).contains('\n - ', times=1
                 )
        new_bad('ba/d'
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - Has slashes\n'
                 ).contains('\n - ', times=1
                 )
        new_bad('ba\\d'
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - Has slashes\n'
                 ).contains('\n - ', times=1
                 )
        new_bad('-bad'
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - Starts with a hyphen\n'
                 ).contains('\n - ', times=1
                 )
        new_bad(' bad '
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - Starts with spaces\n'
                 ).contains(' - Ends with spaces\n'
                 ).contains('\n - ', times=2
                 )
        new_bad(' ba/d '
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - Starts with spaces\n'
                 ).contains(' - Ends with spaces\n'
                 ).contains(' - Has slashes\n'
                 ).contains('\n - ', times=3
                 )
        new_bad(' ba\\d '
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - Starts with spaces\n'
                 ).contains(' - Ends with spaces\n'
                 ).contains(' - Has slashes\n'
                 ).contains('\n - ', times=3
                 )
        new_bad('-ba\\d '
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - Starts with a hyphen\n'
                 ).contains(' - Ends with spaces\n'
                 ).contains(' - Has slashes\n'
                 ).contains('\n - ', times=3
                 )
        with TemporaryDirectory(cd=True) as d:
            os.makedirs(os.path.join(d, 'usedname'))
            new_bad('usedname'
                 ).contains('Invalid name for sub. Errors:'
                 ).contains(' - A file with the same name already exists\n'
                 ).contains('\n - ', times=1
                 )

    def test_new_fat(self):
        with TemporaryDirectory(cd=True) as d:
            sys.argv = ['subdue', 'new', 'mysub']
            with OutStreamCheckedCapture(self) as cap:
                subdue.main()
            cap.stdout.contains(subdue.core.BANNER)
            subroot = os.path.join(d, 'mysub')
            self.assertOsPathIsDir(subroot)
            self.assertOsPathIsDir(os.path.join(subroot, 'bin'))
            self.assertOsPathIsDir(os.path.join(subroot, 'commands'))
            self.assertOsPathIsDir(os.path.join(subroot, 'share'))
            self.assertOsPathIsDir(os.path.join(subroot, 'lib'))

    def test_new_thin(self):
        with TemporaryDirectory(cd=True) as d:
            sys.argv = ['subdue', 'new', '--thin', 'mysub']
            with OutStreamCheckedCapture(self) as cap:
                subdue.main()
            cap.stdout.contains(subdue.core.BANNER)
            subroot = os.path.join(d, 'mysub')
            self.assertOsPathIsDir(subroot)
            self.assertNotOsPathExists(os.path.join(subroot, 'bin'))
            self.assertOsPathIsDir(os.path.join(subroot, 'commands'))
            self.assertOsPathIsDir(os.path.join(subroot, 'share'))
            self.assertOsPathIsDir(os.path.join(subroot, 'lib'))


    def test_new_default_driver(self):
        with TemporaryDirectory(cd=True) as d:
            sys.argv = ['subdue', 'new', 'mysub']
            with OutStreamCheckedCapture(self):
                subdue.main()
            driver = os.path.join(d, 'mysub', 'bin', 'mysub')
            self.assertOsPathIsFile(driver)
            self.assertIsExecutable(driver)
            with open(driver) as f:
                driver_text = f.read()
            self.assertEqual(driver_text, subdue.core.DEFAULT_DRIVER_CODE)


class TestDriverMain(SubdueTestCase):


    def test_vanilla_driver(self):
        """
        Call the driver function directly with no arguments
        """
        with OutStreamCheckedCapture(self) as cap:
            subdue.sub.main([])
        cap.stdout.contains("subdue help")

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
                                root_path=sub_root,
                                command_runner=caller)
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
                return_code = utils.call_driver(sub_root, ['mycommand'])

            self.assertEqual(return_code, 0, "Return code ({}) != expected ({}). Capture: {}".format(return_code, 0, cap))
            cap.stdout.matches(r"^This is foo\n")
