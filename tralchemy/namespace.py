# namespace.py
#
# Copyright (C) 2009, Codethink Ltd.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#
# Author:
#       John Carr <john.carr@unrouted.co.uk>

import os, sys
from types import ModuleType

from .core import types, namespaces

class Namespace(ModuleType):
    """ Class representing a tracker namespace """

    def __init__(self, loader):
        self._loader = loader

    @property
    def __file__(self):
        return self._loader.name

    @property
    def __name__(self):
        return self._loader.name

    @property
    def __path__(self):
        return []

    def __repr__(self):
        return "<namespace %r from %r>" % (self.__name__, self._path)

    def __getattr__(self, name):
        from .core import types
        cls = types.get_class("%s:%s" % (self.__name__, name))
        if not cls:
            raise AttributeError("%r object has no attribute %r" % (
                    self.__class__.__name__, name))

        self.__dict__[name] = cls
        return cls

    def __dir__(self):
        from .core import types
        Class = types.get_class("rdfs:Class")
        members = []
        for cls in Class.get():
            if cls.uri.startswith(self.__name__ + ":"):
                members.append(cls.uri[len(self.__name__)+1:])
        return members

    __all__ = property(__dir__)


class NamespaceFinder(object):
    """ Class to register with python so we can dynamically generate modules """

    def __init__(self, name, path):
        self.name = name
        self.path = path

    @staticmethod
    def find_module(name, path=None):
        names = name.split(".")

        # We only support imports of tralchemy.<namespace_name>
        if len(names) != 2 or names[0] != "tralchemy":
            return None

        # To avoid pain misery and suffering, don't do anything clever for
        # our interals..
        if names[1] in ("core", "namespace"):
            return None

        if not names[1] in namespaces.values():
            return None

        return NamespaceLoader(names[1], path)


class NamespaceLoader(object):

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def load_module(self, name):
        return Namespace(self)


def install_importhook():
    sys.meta_path.append(NamespaceFinder)

