# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys
import inspect
import argparse

from subdue.core import compat
from subdue import builtincmd

class SubPaths(object):
    def __init__(self, root=None):
        # print __file__
        self.calling_script = self._find_calling_script()
        self.name = os.path.basename(self.calling_script)
        self.bin = os.path.dirname(os.path.abspath(self.calling_script))
        self.root = os.path.dirname(self.bin) if root is None else root
        self.commands = os.path.join(self.root, 'commands')
        self.lib = os.path.join(self.root, 'lib')
        self.shared = os.path.join(self.root, 'shared')

    @staticmethod
    def _find_calling_script():
        """
        Inspect the calls stack to determine the path to the script that is
        calling this in the first place.
        """
        # In cPython, the bottom of the callstack has the main script, but in
        # pypy, app_main.py appears in the first three levels.
        for record in reversed(inspect.stack()):
            if record[1] != 'app_main.py':
                return record[1]


    def __repr__(self):
        return """
            ROOT: {0.root}
            LIB: {0.lib}
            BIN: {0.bin}
            COMMANDS: {0.commands}
            """.format(self)


class EnvProp(object):
    def __init__(self, name, doc=None):
        self.name = name

    def __get__(self, obj, objtype):
        return obj._get(self.name)

    def __set__(self, obj, val):
        obj._set(self.name, val)

class Environment(object):

    class SubVar(object):
        def __init__(self, name, value):
            self.name = "_SUB_{varname}_".format(varname=name)
            self.value = value
        def __str__(self):
            return "{self.name}={self.value}".format(self=self)

    def __init__(self, paths):
        self.vars = {}
        self.path = os.environ['PATH'].split(':')

        self.name = paths.name
        self.command = ''
        self.path_root = paths.root
        self.path_shared = paths.shared
        self.path_lib = paths.lib
        self.is_eval = 0

    def prepend_to_path(self, path, immediate=False):
        self.path.insert(0, path)
        if immediate:
            self._apply_path()

    def append_to_path(self, path, immediate=False):
        self.path.append(path)
        if immediate:
            self._apply_path()

    def _apply_path(self):
        new_path = ':'.join(self.path)
        os.environ['PATH'] = new_path

    def _set(self, name, value):
        if value is not None:
            value = compat.unicode(value)
        self.vars[name.lower()] = Environment.SubVar(name.upper(), value)

    def _get(self, name):
        return self.vars.get(name.lower(), None)

    def __str__(self):
        return ", ".join(("{0}:[{1.name}={1.value}]".format(k, v) for k,v in self.vars.items()))


    def save(self):
        for var in compat.itervalues(self.vars):
            os.environ[var.name] = var.value
        self._apply_path()

    name = EnvProp('name')
    command = EnvProp('command')
    path_command = EnvProp('path_command')
    path_root = EnvProp('path_root')
    path_shared = EnvProp('path_shared')
    path_lib = EnvProp('path_lib')
    is_eval = EnvProp('is_eval')
    shell = EnvProp('shell')



class Command(object):
    """
    The representation of a user defined sub command.

    If found is False, then this is an empty placeholder that indicates a
    searched command could not be found.

    """
    def __init__(self, tokens, path, is_sh, is_container, arguments):

        self.tokens = tokens
        """ The tokens that make up the command, excluding the sub name """

        self.path = path
        """ The path to the executable file for this command """

        self.is_sh = is_sh
        """ True when the script was found by prepending the eval prefix to the
        last token """

        self.arguments = arguments
        """ The arguments to pass to the executable for this command """

        self.is_container = is_container

    def run_with(self, runner):
        """
        Execute this command with a given runner, which must take an array of
        argv to run
        """
        runner([self.path] + self.arguments)

    @property
    def is_eval(self):
        """
        True if the command's last token has the eval prefix explicitly
        """
        return self.tokens[-1].startswith('sh-')

    @property
    def found_with_sh(self):
        """
        True if the eval preix was added before the command could be found
        """
        return self.is_sh

    @property
    def found(self):
        """
        Some instances can be used to signal that a command was not found for
        the given tokens. In such cases, the value of :found: is False.
        Otherwise True.
        """
        return self.path is not None

    @property
    def command(self):
        """
        The command, without arguments, as a string. Useful for error messages
        """
        return ' '.join(self.tokens)

    @classmethod
    def create_not_found(cls, tokens):
        """
        Create a sentinel instance to signal that the command was not found for
        a given set of tokens
        """
        return cls(tokens, None, None, None, None)

    def __repr__(self):
        if not self.found:
            return "subdue.sub.Command.create_not_found()"
        return ("subdue.sub.Command(tokens={0.tokens}, "
                "path='{0.path}', "
                "is_eval={0.is_eval}, "
                "found_with_sh={0.found_with_sh}, "
                "is_container={0.is_container}, "
                "arguments={0.arguments})".format(self))



def mkcmd(command, sh_flag=False):
    """
    Return a string with the name of a command in this sub.
    """
    return "sh-%s" % command if sh_flag else command

def find_command_path(argv, paths, start_dir=None):
    """
    Given a command line with tokens representing both the subcommand structure
    and eventually the arguments for a command, figure out the path to the
    command and extract the items from the command line that are to be passed
    as parameters of that command.

    Returns a Command object, which contains:
        * The full path to the command, which can be either a file or a
          directory. This will be None if the command cannot be found.
        * A list of the tokens that lead up to the command, not including the
          arguments for such. This is always set.
        * The arguments to be passed to the command. this will be None if the
          command cannot be found.
    """
    running_path = paths.commands if start_dir is None else start_dir
    shift = 0
    command = []
    is_sh = False
    is_dir = False
    for (shift, token) in enumerate(argv):

        # If we still have not resolved the script name and we are already
        # seeing flags in the command line. This means user passing flags to a
        # container, which is not supported, so just jump out and show help for
        # the container that has been built so far.
        if token[0] == '-':
            break

        command.append(token)
        possible_path = os.path.join(running_path, token)
        is_dir = False

        # If the current token is part of the path but it is not the script
        # itself, just add to running path and keep looking.
        if os.path.isdir(possible_path):
            running_path = possible_path
            is_dir = True
            continue

        # But if the current token is the script, set the path and return.
        if os.access(possible_path, os.X_OK):
            running_path = possible_path
            break

        # Perhaps it's an "sh-type" script
        possible_path_sh = os.path.join(running_path, mkcmd(token, sh_flag=True))
        if os.access(possible_path_sh, os.X_OK):
            running_path = possible_path_sh
            is_sh = True
            break

        # Otherwise, we have a token that is not a directory and appears before
        # the script is found. This is an error. Make sure we still return the
        # command, so it can be shown in the error.
        return Command.create_not_found(command)

    return Command(command, running_path, is_sh, is_dir, argv[shift+1:])

def path_prepend(directory):
    """
    Add a given directory to the beginning of the PATH environment variable.
    """
    os.environ['PATH'] = ":".join((directory, os.environ['PATH']))


def find_builtin_command(args, paths):
    cmd = builtincmd.find(args[0])
    if cmd is not None:
        return cmd(args, paths)

def command_help():
    return True

def execvp_runner(args):
    os.execvp(args[0], args)

def bool_to_rc(result):
    sys.exit(0 if result else 1)


def parse_args(argv):
    """ Parse and validate command line arguments """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--is-eval", action='store_true')
    # The shell function wrapper will use this to inform the driver about the shell:
    parser.add_argument("--shell", help=argparse.SUPPRESS)
    parser.add_argument("-h", "--help", action='store_true')
    parser.add_argument("args", nargs=argparse.REMAINDER)

    args = parser.parse_args(argv)

    return args

def do_main(argv=None, **kwargs):
    """
    Main entry point for a Subdue Sub.

    Undocumented unimplemented parameters:

      * doc_expansions
      * subhelptext
      * presummaryline
      * docfilename
      * summaryformatter
      * helpformatter
      * lookupinpath


    :param list argv: Command line arguments
    :param str root_path: The path to the root of the sub
    :param callable command_runner: A callable to run the found command script

    """

    # Parse command line arguments
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    # Derive all necessary paths
    paths = SubPaths(kwargs.get('sub_path'))

    # Check for the -h or --help option, or no arguments at all: That should
    # print help
    if args.help or not args.args:
        help_cmd = find_builtin_command(['help'], paths)
        help_cmd()
        return 0

    # Sets _SUB_NAME, _SUB_PATH_ROOT_, _SUB_PATH_LIB_, _SUB_PATH_SHARED_
    env = Environment(paths)
    env.shell = args.shell or '' # Sets _SUB_SHELL_

    env.prepend_to_path(paths.lib)
    env.prepend_to_path(paths.bin)

    internal_command = find_builtin_command(args.args, paths)
    if internal_command is not None:
        return internal_command()

    # Try finding the command under the commands directory of the sub
    command = find_command_path(args.args, paths)

    # If we are querying for eval commands, say NO even when the command is not
    # found. This will probably be folowed by a normal call to the command,
    # which will result in the error below.
    if args.is_eval:
        return bool_to_rc(command.found and command.found_with_sh)

    if not command.found:
        sys.exit("{0}: no such command `{1}'".format(paths.name, command.command))

    if command.is_container:
        # TODO: show container help and don't die
        sys.exit("{0}: can't run a container `{1}'".format(paths.name, command.command))
        return 1

    if command.found_with_sh:
        env.is_eval = 1

    env.command = command.command   # _SUB_COMMAND_
    env.path_command = command.path # _SUB_PATH_COMMAND_

    # This will commit all environment changes to the real environment
    env.save()

    api_runner = kwargs.get('command_runner', execvp_runner)
    command.run_with(api_runner)


def main(argv=None, **kwargs):
    api_exit = kwargs.get('exit', True)
    if api_exit:
        # If exit is called, this will result in death of the process.
        # Additionally, exit with anything that do_main returns
        sys.exit(do_main(argv, **kwargs))
    else:
        # Don't exit, return the SystemExit exception instead
        try:
            return do_main(argv, **kwargs)
        except SystemExit as se:
            return se

