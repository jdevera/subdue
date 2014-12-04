# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

registry = {}

def built_in_command(name):
    def wrapper(c):
        registry[name] = c
        return c
    return wrapper


@built_in_command('commands')
class Commands(object):
    def __call__(self, args):
        print ("built-in command: commands")

@built_in_command('help')
class Help(object):
    def __call__(self, args):
        print ("built-in command: help")
