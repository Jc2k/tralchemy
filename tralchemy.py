
import dbus

bus = dbus.SessionBus()
tracker_obj = bus.get_object("org.freedesktop.Tracker", "/org/freedesktop/Tracker/Resources")
tracker = dbus.Interface(tracker_obj, "org.freedesktop.Tracker.Resources")

# Map tracker prefixes to ontology namespaces and back
prefix_to_ns = {}
ns_to_prefix = {}
for prefix, namespace in tracker.SparqlQuery("SELECT ?prefix, ?ns WHERE { ?ns tracker:prefix ?prefix }"):
    prefix_to_ns[prefix] = namespace
    ns_to_prefix[namespace] = prefix

# Map tracker types to python types
types = {
    "http://www.w3.org/2001/XMLSchema#boolean": lambda x: x=='true',
    "http://www.w3.org/2001/XMLSchema#integer": int,
    "http://www.w3.org/2001/XMLSchema#double": float,
    "http://www.w3.org/2000/01/rdf-schema#Literal": str,
    "http://www.w3.org/2001/XMLSchema#string": str,
}

def get_classname(classname):
    """ Takes a classname and flattens it into tracker form """
    if classname.startswith("http://"):
        for ns, prefix in ns_to_prefix.iteritems():
            if classname.startswith(ns):
                return prefix + ":" + classname[len(ns):]
    return classname


class Resource(object):
    """ Everything is a resource """

    _type_ = "rdfs:Resource"

    def __init__(self, uri):
        self.uri = uri

    @classmethod
    def get(cls, **kwargs):
        fragment = ""
        for key, value in kwargs.iteritems():
            key = getattr(cls, key).uri
            fragment += " . ?o %s %s" % (key, value)

        results = tracker.SparqlQuery("SELECT ?o WHERE { ?o rdf:type %s %s}" % (cls._type_, fragment))
        for result in results:
            classname = result[0]
            classname = get_classname(classname)
            yield cls(classname)


class Property(Resource, property):

    _type_ = "rdf:Property"

    def __init__(self, uri, doc=""):
        super(Property, self).__init__(uri)
        self.__doc__ = doc

    def __get__(self, instance, instance_type):
        if instance is None:
            return self

        results = tracker.SparqlQuery("SELECT ?v WHERE { %s %s ?v }" % (instance.uri, self.uri))
        for result in results:
            #FIXME: What to do about lists of stuff. What to do about stuff that isnt a string.
            result = result[0]

            if self.uri == 'rdfs:domain':
                return result
            elif self.domain in types:
                return types[self.domain](result)
            else:
                return result

    def __set__(self, instance, value):
        pass

    def __delete__(self, instance):
        pass

# Now Resource and Property exist, monkey patch them with some properties
Resource.comment = Property("rdfs:comment")
Resource.label = Property("rdfs:label")
Resource.type = Property("rdf:type")

Property.domain = Property("rdfs:domain")
Property.subpropertyof = Property("rdfs:subPropertyOf")
Property.range = Property("rdfs:range")
Property.indexed = Property("tracker:indexed")
Property.fulltextindexed = Property("tracker:fulltextIndexed")
Property.transient = Property("tracker:transient")


class Class(Resource):

    _type_ = "rdfs:Class"

    subclassof = Property("rdfs:subClassOf")
    notify = Property("tracker:notify")



class WrapperFactory(object):

    def __init__(self):
        # Cache previous generated objects
        self.wrapped = {}

        # Connection to tracker
        self.bus = dbus.SessionBus()
        tracker_object = self.bus.get_object("org.freedesktop.Tracker", "/org/freedesktop/Tracker/Resources")
        self.tracker = dbus.Interface(tracker_object, "org.freedesktop.Tracker.Resources")

        for cls in (Class, Property, Resource):
            self.wrapped[cls._type_] = cls

    def get_class(self, classname):
        classname = get_classname(classname)

        if classname in self.wrapped:
            return self.wrapped[classname]

        # Look up this class in tracker
        cls = Class(classname)

        attrs = {
            "_type_": cls.uri,
            "__doc__": cls.comment or ""
        }

        # FIXME: subclassof should return an object!!
        baseclass = cls.subclassof
        if baseclass:
            baseclass = [self.get_class(baseclass)]
        else:
            baseclass = [Resource]

        for prop in Property.get(domain=cls.uri):
            if prop.label:
                attrs[prop.label.lower().replace(" ", "_")] = prop

        # Make a new class
        klass = type(str(classname), tuple(baseclass), attrs)

        # Cache it for later
        self.wrapped[klass._type_] = klass

        return klass


if __name__ == "__main__":
    w = WrapperFactory()
    #help(w.get_class("rdfs:Resource"))
    #help(w.get_class("rdfs:Class"))
    self = __import__(__name__)
    for cls in Class.get():
        cls = w.get_class(cls.uri)
        setattr(self, cls.__name__, cls)
    help(self)

    foo = {}
    for p in Property.get():
        foo.setdefault(p.range, 0)
        foo[p.range] += 1

    for k, v in foo.items():
        print k, v

