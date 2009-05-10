
import dbus

class WrapperFactory(object):

    def __init__(self):
        # Cache previous generated objects
        self.wrapped = {}

        # Connection to tracker
        self.bus = dbus.SessionBus()
        tracker_object = self.bus.get_object("org.freedesktop.Tracker", "/org/freedesktop/Tracker/Resources")
        self.tracker = dbus.Interface(tracker_object, "org.freedesktop.Tracker.Resources")

        # Map tracker prefixes to ontology namespaces and back
        self.prefix_to_ns = {}
        self.ns_to_prefix = {}
        for prefix, namespace in self.tracker.SparqlQuery("SELECT ?prefix, ?ns WHERE { ?ns tracker:prefix ?prefix }"):
            self.prefix_to_ns[prefix] = namespace
            self.ns_to_prefix[namespace] = prefix

    def get_classname(self, classname):
        """ Takes a classname and flattens it into tracker form """
        if classname.startswith("http://"):
            for ns, prefix in self.ns_to_prefix.iteritems():
                if classname.startswith(ns):
                    return prefix + ":" + classname[len(ns):]
        return classname

    def get_class(self, classname):
        classname = self.get_classname(classname)
        print classname

        if classname in self.wrapped:
            return self.wrapped[classname]

        attrs = {}
        baseclass = [object]

        # Get class.. metadata..
        results = self.tracker.SparqlQuery("SELECT ?k ?v WHERE { %s ?k ?v }" % classname)
        for key, value in results:
            if key == "http://www.w3.org/2000/01/rdf-schema#comment":
                attrs['__doc__'] = value
            elif key == "http://www.w3.org/2000/01/rdf-schema#subClassOf":
                baseclass = [self.get_class(value)]
            else:
                print key, value

        # Get all properties of this class
        properties = self.tracker.SparqlQuery("SELECT ?prop ?label ?comment WHERE { ?prop rdfs:domain %s . ?prop rdfs:label ?label . ?prop rdfs:comment ?comment }" % classname)
        for name, label, comment in properties:
            def getter(self):
                return "badgers"
            def setter(self, value):
                pass
            prop = property(fget=getter, fset=setter, doc=comment)
            attrs[label.lower().replace(" ", "_")] = prop

        # Make a new class
        klass = type(str(classname), tuple(baseclass), attrs)

        # Cache it for later
        self.wrapped[classname] = klass

        return klass

    def get_all(self):
        results = self.tracker.SparqlQuery("SELECT ?o WHERE { ?o rdf:type rdfs:Class }")
        for result in results:
            classname = result[0]
            klass = self.get_class(classname)

if __name__ == "__main__":
    w = WrapperFactory()
    #help(w.get_class("rdfs:Resource"))
    help(w.get_class("rdfs:Class"))
    #w.get_all()
