from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import unittest
import sys
import os
import tempfile
import shutil
import subprocess
import textwrap

import subdue
from subdue.core import compat
from .compat import which

__unittest = None



class TextChecker(compat.UnicodeMixin):

    def __init__(self, testcase, text):
        self.text = text
        self.tc = testcase

    def anchor_pattern(self, pattern):
        new_pattern = [pattern]
        if not pattern.startswith('^'):
            new_pattern.insert(0, r'^')
        if not pattern.endswith('$'):
            new_pattern.append(r'$')
        return ''.join(new_pattern)


    def matches(self, pattern, anchored=False):
        if anchored:
            pattern = self.anchor_pattern(pattern)
        assertRegex = getattr(self.tc, 'assertRegex',
                              self.tc.assertRegexpMatches)
        assertRegex(self.text, pattern)
        return self

    def not_matches(self, pattern, anchored=False):
        if anchored:
            pattern = self.anchor_pattern(pattern)
        assertNotRegex = getattr(self.tc, 'assertNotRegex',
                                 self.tc.assertNotRegexpMatches)
        assertNotRegex(self.text, pattern)
        return self

    def contains(self, pattern, times=None):
        self.tc.assertIn(pattern, self.text)
        if times is None:
            return self
        appears = self.text.count(pattern)
        if times != appears:
            msg = self.tc._formatMessage(None,
                "%s appears only %d of the %d expected times in %s" % (
                unittest.util.safe_repr(pattern),
                appears, times,
                unittest.util.safe_repr(self.text)
                ))
            raise self.tc.failureException(msg)
        return self

    def not_contains(self, pattern):
        self.tc.assertNotIn(pattern, self.text)
        return self

    def is_empty(self):
        return self.matches(r'^$')

    def __unicode__(self):
        return self.text


class TemporaryDirectory(object):
    """
    A context manager to create a temporary directory and, optionally, cd into
    it.
    """

    def __init__(self, cd=False, *args, **kwargs):
        self.name = tempfile.mkdtemp(*args, **kwargs)
        self.cd = cd

    def __enter__(self):
        if self.cd:
            self.prev_dir = os.getcwd()
            os.chdir(self.name)
        return self.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cd:
            os.chdir(self.prev_dir)
        shutil.rmtree(self.name)



class OutStreamCapture(compat.UnicodeMixin):
    """
    A context manager to replace stdout and stderr with StringIO objects and
    cache all output.
    """

    def __init__(self):
        self._stdout = None
        self._stderr = None
        self.stdout = None
        self.stderr = None

    def __enter__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = compat.StringIO()
        sys.stderr = compat.StringIO()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Restore original values of stderr and stdout.
        The captured contents are stored as strings in the stdout and stderr
        members.
        """
        self.stdout = sys.stdout.getvalue()
        self.stderr = sys.stderr.getvalue()
        sys.stdout = self._stdout
        sys.stderr = self._stderr

    def __unicode__(self):
        return "\n".join([
            'STDOUT:',
            compat.unicode(self.stdout),
            'STDERR:',
            compat.unicode(self.stderr)
            ])



class OutStreamCheckedCapture(OutStreamCapture):
    """
    A context manager to cache output. Use when checks are to be performed on
    the output.
    """

    def __init__(self, testcase):
        super(OutStreamCheckedCapture, self).__init__()
        self.tc = testcase

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        The captured contents are wrapped in TextChecker and accessible through
        the stdout and stderr members.
        """
        super(OutStreamCheckedCapture, self).__exit__(
                exc_type, exc_val, exc_tb)
        self.stdout = TextChecker(self.tc, self.stdout)
        self.stderr = TextChecker(self.tc, self.stderr)

class TempSub(TemporaryDirectory):

    class Sub(object):

        class OutCapture(OutStreamCheckedCapture):
            def __init__(self, parent):
                super(TempSub.Sub.OutCapture, self).__init__(parent.testcase)
                self.sub_root = parent.sub_root
                self.name = parent.name
                self.testcase = parent.testcase
                self.return_code = None
                self.command = None

            def assertSucess(self, msg=None):
                self.testcase.assertEqual(self.return_code, 0,
                    msg if msg is not None else 'Expected success (rc = 0) but failed with rc: {}. STDERR: {}'.format(self.return_code, self.stderr))
                return self

            def assertFailure(self, msg=None):
                self.testcase.assertNotEqual(self.return_code, 0,
                    msg if msg is not None else 'Expected failure (rc = 0) but succeeded with rc: {}. STDERR: {}'.format(self.return_code, self.stderr))
                return self

        class Command(object):
            def __init__(self, parent, command):
                self.command = list(command.split('/'))
                """List of command tokens"""
                self.sub = parent

            def run_it(self, *args):
                return self.sub.run(*(self.command + list(args)))


        def __init__(self, parent):
            self.sub_root = parent.subroot
            self.name = parent.subname
            self.testcase = parent.testcase
            self.thin = parent.thin

        def create_subcommand(self, name, interpreter='sh', contents=''):
            create_subcommand(self.sub_root, name, contents, interpreter)
            return TempSub.Sub.Command(self, name)

        def run(self, *args):
            args = list(args)
            with TempSub.Sub.OutCapture(self) as cap:
                if self.thin:
                    # Don't use exec or we'll ruin the tests:
                    caller = SubprocessCaller()
                    subdue.sub.main(args, sub_path=self.sub_root, exit=False, command_runner=caller)
                    rc = caller.returncode
                else:
                    rc = call_driver_for(self.sub_root, args)
            cap.return_code = rc
            cap.command = args
            return cap

    def __init__(self, testcase, name, thin=False):
        super(TempSub, self).__init__(cd=True)
        self.testcase = testcase
        self.subname = name
        self.subroot = os.path.join(self.name, self.subname)
        self.thin = thin

    def __enter__(self):
        super(TempSub, self).__enter__()
        with OutStreamCapture():
            subdue.main(['subdue', 'new', self.subname])
        return TempSub.Sub(self)




class SubdueTestCase(unittest.TestCase):

    def assertOsPathIsDir(self, path, msg=None):
        if not os.path.isdir(path):
            msg = self._formatMessage(msg,
                    "%s is not a directory" % unittest.util.safe_repr(path))
            raise self.failureException(msg)
    def assertNotOsPathIsDir(self, path, msg=None):
        if os.path.isdir(path):
            msg = self._formatMessage(msg,
                    "%s is a directory" % unittest.util.safe_repr(path))
            raise self.failureException(msg)
    def assertOsPathIsFile(self, path, msg=None):
        if not os.path.isfile(path):
            msg = self._formatMessage(msg,
                    "%s is not a file" % unittest.util.safe_repr(path))
            raise self.failureException(msg)
    def assertNotOsPathIsFile(self, path, msg=None):
        if os.path.isfile(path):
            msg = self._formatMessage(msg,
                    "%s is a file" % unittest.util.safe_repr(path))
            raise self.failureException(msg)
    def assertOsPathExists(self, path, msg=None):
        if not os.path.exists(path):
            msg = self._formatMessage(msg,
                    "%s does not exist" % unittest.util.safe_repr(path))
            raise self.failureException(msg)
    def assertNotOsPathExists(self, path, msg=None):
        if os.path.exists(path):
            msg = self._formatMessage(msg,
                    "%s exists" % unittest.util.safe_repr(path))
            raise self.failureException(msg)
    def assertIsExecutable(self, path, msg=None):
        if not os.access(path, os.X_OK):
            msg = self._formatMessage(msg,
                    "%s is not executable" % unittest.util.safe_repr(path))
            raise self.failureException(msg)


def subprocess_call(args, **kwargs):
    """
    Capture friendly subprocess call.
    When stdout and stderr are being captured, replaced by StringIO objects,
    these cannot be passed to subprocess calls directly, since they expect a
    real file.

    So this pipes stdout and stderr and reads the contents after execution as a
    string, writing it to whatever is set as sys.stdout and sys.stderr

    This also works if sys.stdout and sys.stderr are not redirected
    """

    # If there is no redirection, just use "call" directly
    if sys.stdout == sys.__stdout__ and sys.stderr == sys.__stderr__:
        return subprocess.call(args, **kwargs)

    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.PIPE
    proc = subprocess.Popen(args, **kwargs)
    (stdout, stderr) = proc.communicate()
    if stdout:
        sys.stdout.write(stdout.decode('utf8'))
    if stderr:
        sys.stderr.write(stderr.decode('utf8'))

    return proc.returncode

class SubprocessCaller(object):
    def __init__(self):
        self.returncode = None
    def __call__(self, args, **kwargs):
        self.returncode = subprocess_call(args, **kwargs)


def create_subcommand(sub_root, name, contents, interpreter=None):
    contents = textwrap.dedent(contents)
    if interpreter is not None:
        interp_path = which(interpreter)
        contents = '#!{}\n{}\n'.format(interp_path, contents)

    name_parts = name.split('/')
    sub_command_file = os.path.join(sub_root, 'commands', *name_parts)
    sub_command_dir = os.path.dirname(sub_command_file)
    if not os.path.exists(sub_command_dir):
        os.makedirs(sub_command_dir)
    with open(sub_command_file, 'w') as cmdfile:
        cmdfile.write(contents)
    os.chmod(sub_command_file, 448) # 0700, for python 2.7 vs 3.X compat


def call_driver_for(sub_root, args=None, **kwargs):
    if args is None:
        args = []
    sub_name = os.path.basename(sub_root)
    sub_driver = os.path.join(sub_root, 'bin', sub_name)
    return call_driver(sub_driver, args, **kwargs)

def call_driver(sub_driver, args=None, **kwargs):
    # Get the environment and add the subdue path to the PYTHONPATH
    env = kwargs.get('env', os.environ).copy()
    subdue_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env['PYTHONPATH'] = ':'.join([env.get('PYTHONPATH', ''), subdue_path])
    kwargs['env'] = env

    return_code = subprocess_call([sub_driver] + args, **kwargs)
    return return_code

def call_thin(sub_root, args=None, **kwargs):
    if args is None:
        args = []
    # Don't use exec or we'll ruin the tests:
    caller = SubprocessCaller()
    subdue.sub.main(args, sub_path=sub_root, exit=False, command_runner=caller)
    return caller.returncode
