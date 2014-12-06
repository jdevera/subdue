# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from . import base

from . import help
from . import commands
from . import init

__all__ = ['find']

def find(name):
    return base.registry.get(name)

