#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

__description__ = ''

import sys
import argparse
import os
import stat

from subdue import core




REQUIRED_DIRECTORIES = [
    'commands',
    'lib',
    'share',
]

DIRECTORIES = ['bin'] + REQUIRED_DIRECTORIES

CREATE_SUCCESS_THIN = """

Note: This is a thin sub, before using it you need to create a driver.

Please see the documentation for more information on custom drivers.
Once the driver is created, you can set this sub up with:

  <path-to-driver> init

You can convert this thin sub to a regular sub by running:
  subdue modify --fat {0}
"""


def command(f):
    return f


@command
def new(args):
    """
    Create a new sub
    """
    check_sub_name(args.subname)
    print(core.color.bright_blue(core.BANNER))
    print("Creating {0}sub '{1}'...\n".format(
        'thin ' if args.thin else '', args.subname))
    root = os.path.abspath(args.subname)
    directories = REQUIRED_DIRECTORIES if args.thin else DIRECTORIES

    for d in directories:
        sd = os.path.join(root, d)
        if args.verbose:
            print("Creating directory {0}".format(os.path.relpath(sd)))
        os.makedirs(sd)

    if not args.thin:
        driver = create_default_driver(root, args.subname, args.verbose)

    print(core.color.bright(
        "Congratulations! Your sub '{0}' is ready!\n".format(args.subname)))
    if args.thin:
        print(CREATE_SUCCESS_THIN.format(args.subname))
    else:
        print("You can set it up by running:")
        print("  {0} init".format(os.path.relpath(driver)))
    return root


@command
def check(args):
    root = os.path.abspath(args.subname)

    errors = []
    if not os.path.isdir(root):
        errors.append("Not a directory: {0}".format(args.subname))

    directories = REQUIRED_DIRECTORIES if args.thin else DIRECTORIES

    for d in directories:
        sd = os.path.join(root, d)
        if not os.path.isdir(sd):
            errors.append("Required directory {0} is missing".format(d))
    if args.thin and os.path.isdir(os.path.join(root, 'bin')):
        errors.append("Thin sub should not have a 'bin' directory")

    if errors:
        core.die("Errors found in {0}:\n - {1}".format(
            args.subname, "\n - ".join(errors)))


def create_default_driver(root, subname, verbose=False):
    driver = os.path.join(root, 'bin', subname)
    if verbose:
        print("Creating driver {0}".format(driver))
    with open(driver, "w") as f:
        f.write(core.DEFAULT_DRIVER_CODE.lstrip())

    # Make executable by current user
    if verbose:
        print("Making the driver executable")
    os.chmod(driver, os.stat(driver).st_mode | stat.S_IXUSR)
    return driver


def check_sub_name(name):
    errors = []
    if name != name.rstrip():
        errors.append("Ends with spaces")
    if name != name.lstrip():
        errors.append("Starts with spaces")
    if name.startswith('-'):
        errors.append("Starts with a hyphen")
    if '/' in name or '\\' in name:
        errors.append("Has slashes")
    if not errors and os.path.exists(os.path.abspath(name)):
        errors.append("A file with the same name already exists")
    if errors:
        core.die("Invalid name for sub. Errors: \n - {0}".format(
                 "\n - ".join(errors)))


def populate_example(root):
    print("Creating example files for {0}".format(root))


def parse_args(argv):
    """
    Parse and validate command line arguments
    """

    def add_flag(parser, short, longn, help, default=False):
        parser.add_argument(
                short, longn, action='store_true', default=default, help=help)

    # Augment the ArgumentParser class with the convenience add_flag method
    argparse.ArgumentParser.add_flag = add_flag

    parser = argparse.ArgumentParser(description=__description__)

    parser.add_flag("-v", "--verbose", help="Give extra information about steps")

    subparsers = parser.add_subparsers(dest='subcommand')

    new = subparsers.add_parser('new')

    new.add_argument( "subname", metavar="SUB_NAME", help="Name of the sub to create")
    new.add_flag("-x", "--example", help="Create an example sub, with some sample contents")
    new.add_flag("-t", "--thin", help="Create a thin sub, without a driver")

    check = subparsers.add_parser('check')
    check.add_argument( "subname", metavar="SUB_NAME", help="Name of the sub to check")
    check.add_flag("-t", "--thin", help="Consider the sub as thin")

    modify = subparsers.add_parser('modify')
    modify.add_argument("subname", metavar="SUB_NAME", help="Name of the sub to modify")
    modify.add_flag("-t", "--thin", help="Turn this fat sub into a thin sub")
    modify.add_flag("-f", "--fat", help="Turn this thin sub into a fat sub")

    args = parser.parse_args(argv[1:])
    if args.subcommand is None:
        parser.error("too few arguments")

    return args


def main(argv=None):
    """
    Run this program
    """
    if argv is None:
        argv = sys.argv

    args = parse_args(argv)
    try:
        if args.verbose:
            core.verbose = True
        if args.subcommand == 'new':
            root = new(args)
            if args.example:
                populate_example(root)
        elif args.subcommand == 'check':
            check(args)

    except KeyboardInterrupt:
        sys.exit(-1)


if __name__ == '__main__':
    sys.exit(main(sys.argv) or 0)
