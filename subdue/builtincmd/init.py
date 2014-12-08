from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import pkgutil
import string
import os
import sys

from . import base

TEMPLATES_PACKAGE = 'subdue.builtincmd.templates'

SUPPORTED_SHELLS = [
        'bash',
    ]

def guess_shell():
    """
    Naive attempt at guessing the calling shell by simply exploring the SHELL
    environment variable.
    """
    shell = os.environ.get('SHELL', None)
    if shell is not None and os.path.exists(shell):
        shell = os.path.basename(shell)
    else:
        shell = None
    return shell


def parse_args(argv):
    """ Parse and validate command line arguments """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--full", action='store_true', help=argparse.SUPPRESS)
    parser.add_argument("--shell", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if not args.shell:
        args.shell = guess_shell()
        if not args.shell:
            sys.exit("A shell was not specified and could not be inferred from the environment")
    if args.shell and args.shell not in SUPPORTED_SHELLS:
        sys.exit(
            "Shell {} is not supported. Supported shells are: {}".format(
                args.shell, ", ".join(SUPPORTED_SHELLS)))
    # TODO: Improve these conditions + error messages

    return args


@base.built_in_command('init')
class Init(base.BuiltInCommand):

    def __init__(self, args, paths):
        super(Init, self).__init__(args, paths)

    def __call__(self):
        args = parse_args(self.args[1:])
        if args.full:
            return self.do_full_mode(args.shell)
        self.do_simple_mode(args.shell)

    def do_simple_mode(self, shell):
        simple_tpl_name = 'init_simple_{}.tpl'.format(shell)
        print(self.eval_template(simple_tpl_name))

    def do_full_mode(self, shell):
        full_tpl_name = 'init_full_{}.tpl'.format(shell)
        print(self.eval_template(full_tpl_name))

    def make_template_mapping(self):
        return {
            'sub_name' : self.paths.name,
            'sub_bin' : os.path.abspath(self.paths.calling_script),
            'sub_bin_dir' : self.paths.bin,
            }

    def eval_template(self, name, **kwargs):
        tpl = pkgutil.get_data(TEMPLATES_PACKAGE, name)
        mapping = self.make_template_mapping()
        return string.Template(tpl).safe_substitute(mapping, **kwargs)

