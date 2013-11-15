import unittest
import sys
import os
import tempfile
import StringIO
import shutil

__unittest = None


class TextChecker(object):

    def __init__(self, testcase, text):
        self.text = text
        self.tc = testcase

    def matches(self, pattern):
        self.tc.assertRegexpMatches(self.text, pattern)
        return self

    def not_matches(self, pattern):
        self.tc.assertNotRegexpMatches(self.text, pattern)
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

    def __unicode__(self):
        return self.text

    def __str__(self):
        return self.__unicode__().encode('utf-8')


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


class OutStreamCapture(object):
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
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
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

