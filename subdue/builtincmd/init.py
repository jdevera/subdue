from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

from . import base

@base.built_in_command('init')
class Init(base.BuiltInCommand):
    def __init__(self, args, paths):
        super(Init, self).__init__(args, paths)

    def __call__(self):
        pass
