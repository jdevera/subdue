import os
import sys
import inspect

class SubPaths(object):
    def __init__(self, root=None):
        # print __file__
        calling_script = inspect.stack()[-1][1]
        self.name = os.path.basename(calling_script)
        self.bin = os.path.dirname(os.path.abspath(calling_script))
        self.root = os.path.dirname(self.bin) if root is None else root
        self.commands = os.path.join(self.root, 'commands')
        self.lib = os.path.join(self.root, 'lib')

    def __repr__(self):
        return """
            ROOT: {0.root}
            LIB: {0.lib}
            BIN: {0.bin}
            COMMANDS: {0.commands}
            """.format(self)


class Command(object):
    def __init__(self, tokens, path, is_sh, arguments):
        self.tokens = tokens
        self.path = path
        self.is_sh = is_sh
        self.arguments = arguments

    def run_with(self, runner):
        runner([self.path] + self.arguments)

    @property
    def found(self):
        return self.path is not None

    @property
    def command(self):
        return ' '.join(self.tokens)

    @classmethod
    def create_not_found(cls, tokens):
        return cls(tokens, None, None, None)

    def __repr__(self):
        if not self.found:
            return "subdue.sub.Command.create_not_found()"
        return ( "subdue.sub.Command(tokens={0.tokens}, path='{0.path}', "
                 "is_sh={0.is_sh}, arguments={0.arguments})".format(self) )



def mkcmd(command, sh_flag = False):
    """
    Return a string with the name of a command in this sub.
    """
    return u"sh-%s" % command if sh_flag else unicode(command)

def find_command_path(argv, paths, start_dir = None):
    """
    Given a command line with tokens representing both the subcommand structure
    and eventually the arguments for a command, figure out the path to the
    command and extract the items from the command line that are to be passed
    as parameters of that command.

    Returns a tuple with the following:
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
    for (shift, token) in enumerate(argv):

        # If we still have not resolved the script name and we are already
        # seeing flags in the command line. This means user passing flags to a
        # container, which is not supported, so just jump out and show help for
        # the container that has been built so far.
        if token[0] == '-':
            break
        command.append(token)
        possible_path = os.path.join(running_path, token)

        # If the current token is part of the path but no the script, just add
        # to running path and keep looking.
        if os.path.isdir(possible_path):
            running_path = possible_path
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
        # return (None, command, None, None)
        return Command.create_not_found(command)

    return Command(command, running_path, is_sh, argv[shift+1:])

def path_prepend(directory):
    """
    Add a given directory to the beginning of the PATH environment variable.
    """
    os.environ['PATH'] = u"%s:%s" % (directory, os.environ['PATH'] )

def command_help():
    print "subdue help"
    return True

def execvp_runner(args):
    os.execvp(args[0], args)

def die(error):
    """
    Show message on stderr and exit
    """
    sys.stderr.write(error)
    sys.stderr.write("\n")
    sys.stderr.flush()
    sys.exit(1)

def main(argv=None, **kwargs):
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
    if argv is None:
        argv = sys.argv[1:]

    paths = SubPaths(kwargs.get('root_path'))
    runner = kwargs.get('command_runner', execvp_runner)

    # path_prepend(paths.lib)
    # path_prepend(paths.bin)

    if len(argv) < 1 or argv[0] in ('-h', '--help'):
        ret = command_help()
        return 0 if ret else 1


    command = find_command_path(argv, paths)
    if not command.found:
        die("{0}: no such command `{1}'".format(paths.name, command.command))
    command.run_with(runner)

