
import dbus

class Resource(object):
    """ Everything is a resource """

    _type_ = "rdfs:Resource"

    def __init__(self, uri):
        self.uri = uri

    @classmethod
    def get(cls, **kwargs):
        results = cls.get_tracker().SparqlQuery("SELECT ?o WHERE { ?o rdf:type %s }" % cls._type_)
        for result in results:
            classname = result[0]
            yield cls(classname)

    @staticmethod
    def get_tracker():
        #FIXME: Share this bit
        bus = dbus.SessionBus()
        tracker = bus.get_object("org.freedesktop.Tracker", "/org/freedesktop/Tracker/Resources")
        return dbus.Interface(tracker, "org.freedesktop.Tracker.Resources")


class Property(Resource, property):

    _type_ = "rdfs:Property"

    def __init__(self, uri, doc=""):
        super(Property, self).__init__(uri)
        self.__doc__ = doc

    def __get__(self, obj, cls):
        results = self.get_tracker().SparqlQuery("SELECT ?v WHERE { %s %s ?v }" % (obj.uri, self.uri))
        for result in results:
            #FIXME: What to do about lists of stuff. What to do about stuff that isnt a string.
            return result[0]

    def __set__(self, obj, value):
        pass

    def __delete__(self, obj):
        pass


class Class(Resource):

    _type_ = "rdfs:Class"

    subclassof = Property("rdfs:subClassOf")
    comment = Property("rdfs:comment")
    label = Property("rdfs:label")
    type = Property("rdf:type")
    notity = Property("tracker:notify")


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

        self.wrapped[Class._type_] = Class
        self.wrapped[Property._type_] = Property
        self.wrapped[Resource._type_] = Resource

    def get_classname(self, classname):
        """ Takes a classname and flattens it into tracker form """
        if classname.startswith("http://"):
            for ns, prefix in self.ns_to_prefix.iteritems():
                if classname.startswith(ns):
                    return prefix + ":" + classname[len(ns):]
        return classname

    def get_class(self, classname):
        classname = self.get_classname(classname)

        if classname in self.wrapped:
            return self.wrapped[classname]

        attrs = {
            "_type_": classname,
        }

        baseclass = [Resource]

        # Get class.. metadata..
        results = self.tracker.SparqlQuery("SELECT ?k ?v WHERE { %s ?k ?v }" % classname)
        for key, value in results:
            if key == "http://www.w3.org/2000/01/rdf-schema#comment":
                attrs['__doc__'] = value
            elif key == "http://www.w3.org/2000/01/rdf-schema#subClassOf":
                baseclass = [self.get_class(value)]

        # Get all properties of this class
        properties = self.tracker.SparqlQuery("SELECT ?prop ?label ?comment WHERE { ?prop rdfs:domain %s . ?prop rdfs:label ?label . ?prop rdfs:comment ?comment }" % classname)
        for name, label, comment in properties:
            prop = Property(name, comment)
            attrs[label.lower().replace(" ", "_")] = prop

        # Make a new class
        klass = type(str(classname), tuple(baseclass), attrs)

        # Cache it for later
        self.wrapped[klass.type] = klass

        return klass

    def get_all(self):
        for cls in Class.get():
            yield self.get_class(cls.uri)

if __name__ == "__main__":
    w = WrapperFactory()
    #help(w.get_class("rdfs:Resource"))
    #help(w.get_class("rdfs:Class"))
    self = __import__(__name__)
    for cls in w.get_all():
        setattr(self, cls.__name__, cls)
    help(self)

