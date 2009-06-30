
import os, sys, types


class Namespace(types.ModuleType):
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
        from .core import WrapperFactory
        cls = WrapperFactory().get_class("%s:%s" % (self.__name__, name))
        cls.__module__ = self.__name__
        if not cls:
            raise AttributeError("%r object has no attribute %r" % (
                    self.__class__.__name__, name))

        self.__dict__[name] = cls
        return cls

    def __dir__(self):
        from .core import WrapperFactory
        Class = WrapperFactory().get_class("rdfs:Class")
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
        #FIXME: This function is a bit of a hack
        if not "tralchemy." in name:
            return None
        name = name[name.find("tralchemy.")+10:]
        if name in ('namespace', 'core', 'dbus', 'uuid', 'query', 'types', 'opcode', 'dis', 'sys', 'dateutil'):
            return None
        if '.' in name:
            return None
        return NamespaceLoader(name, path)


class NamespaceLoader(object):

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def load_module(self, name):
        return Namespace(self)


def install_importhook():
    sys.meta_path.append(NamespaceFinder)

