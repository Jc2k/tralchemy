
import os, sys


class Namespace(object):
    """ Class representing a tracker namespace """

    def __init__(self, namespace, path):
        self._namespace = namespace
        self._path = path

    @property
    def __file__(self):
        return self._namespace

    @property
    def __name__(self):
        return self._namespace

    @property
    def __path__(self):
        return [os.path.dirname(self.__file__)]

    def __repr__(self):
        return "<namespace %r from %r>" % (self._namespace, self._path)

    def __getattr__(self, name):
        from .core import WrapperFactory
        cls = WrapperFactory().get_class("%s:%s" % (self._namespace, name))
        if not cls:
            raise AttributeError("%r object has no attribute %r" % (
                    self.__class__.__name__, name))

        self.__dict__[name] = cls
        return value

    @property
    def __members__(self):
        r = []
        #FIXME: Return names of all objects defined in this namespace
        return r


class Importer(object):
    """ Class to register with python so we can dynamically generate modules """

    def __init__(self, name, path):
        self.name = name
        self.path = path

    @staticmethod
    def find_module(name, path=None):
        #FIXME: This function is a bit of a hack
        if not name.startswith("tralchemy."):
            return None
        name = name[10:]
        if name in ('namespace', 'core', 'dbus', 'uuid'):
            return None
        if '.' in name:
            return None
        return Importer(name, path)

    def load_module(self, name):
        return Namespace(self.name, self.path)


def install_importhook():
    sys.meta_path.append(Importer)

