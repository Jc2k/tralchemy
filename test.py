
import dbus

class WrapperFactory(object):

    def __init__(self):
        # Cache previous generated objects
        self.wrapped = {}

        # Connection to tracker
        self.bus = dbus.SessionBus()
        tracker_object = self.bus.get_object("org.freedesktop.Tracker", "/org/freedesktop/Tracker/Resources")
        self.tracker = dbus.Interface(tracker_object, "org.freedesktop.Tracker.Resources")

    def get_class(self, classname):
        results = self.tracker.SparqlQuery("SELECT ?k ?v WHERE { %s ?k ?v }" % classname)

        attrs = {}
        baseclass = None

        for key, value in results:
            if key == "":
                attrs['__doc__'] = value

if __name__ == "__main__":
    w = WrapperFactory()
    w.get_class("rdfs:Resource")
    w.get_class("rdfs:Class")
