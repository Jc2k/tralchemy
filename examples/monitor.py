
import dbus
from dbus.mainloop.glib import DBusGMainLoop
loop=DBusGMainLoop(set_as_default=True)

import glib

import tralchemy
from tralchemy.rdfs import Class

if __name__ == '__main__':
    for cls in Class.get(notify="true"):
        def added(subjects):
            print cls.uri, subjects
        def changed(subjects):
            print cls.uri, subjects
        def removed(subjects):
            print cls.uri, subjects
        kls = tralchemy.core.types.get_class(cls.uri)
        kls.added.subscribe(added)
        kls.changed.subscribe(changed)
        kls.removed.subscribe(removed)

    loop = glib.MainLoop()
    loop.run()
