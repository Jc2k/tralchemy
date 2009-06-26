# core.py
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

import dbus
import uuid

bus = dbus.SessionBus()
tracker_obj = bus.get_object("org.freedesktop.Tracker", "/org/freedesktop/Tracker/Resources")
tracker = dbus.Interface(tracker_obj, "org.freedesktop.Tracker.Resources")

# Map tracker prefixes to ontology namespaces and back
prefix_to_ns = {}
ns_to_prefix = {}
for prefix, namespace in tracker.SparqlQuery("SELECT ?prefix, ?ns WHERE { ?ns tracker:prefix ?prefix }"):
    prefix_to_ns[prefix] = namespace
    ns_to_prefix[namespace] = prefix

def get_classname(classname):
    """ Takes a classname and flattens it into tracker form """
    if classname.startswith("http://"):
        for ns, prefix in ns_to_prefix.iteritems():
            if classname.startswith(ns):
                return prefix + ":" + classname[len(ns):]
    return classname


class Notifications(object):
    """ Class to allow users to attach signals to a class of object """
    def __init__(self, uri):
        self.uri = uri.replace(":", "/")

    def connect(self, signal, callback):
        def _(subjects):
            subjects = [str(subject) for subject in subjects]
            return callback(subjects)
        bus.add_signal_receiver (_, signal_name=signal,
                                 dbus_interface="org.freedesktop.Tracker.Resources.Class",
                                 path="/org/freedesktop/Tracker/Resources/Classes/%s" % self.uri)


class Resource(object):
    """ Everything is a resource """

    _type_ = "rdfs:Resource"

    def __init__(self, uri):
        self.uri = get_classname(uri)
        self.triples = {}

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

    @classmethod
    def create(cls, **kwargs):
        o = cls(kwargs.get('uid', 'http://localhost/resource/%s' % str(uuid.uuid4())))
        for k, v in kwargs.iteritems():
            if k == "uid" or k =="commit":
                continue
            setattr(o, k, v)
        if not 'commit' in kwargs or kwargs['commit'] == True:
            o.commit()
        return o

    def delete(self):
        tracker.SparqlUpdate("DELETE { <%s> a %s. }" % (self.uri, self._type_))

    def commit(self):
        query = "INSERT { <%s> a %s" % (self.uri, self._type_)
        for k, v in self.triples.iteritems():
            query += " ; %s %s" % (k, v)
        query += " . }"
        tracker.SparqlUpdate(query)
        self.triples = {}


class Property(Resource, property):

    _type_ = "rdf:Property"

    def __init__(self, uri, doc=""):
        super(Property, self).__init__(uri)
        if self.uri != 'rdfs:comment' and self.comment:
            self.__doc__ = "%s\n\n@type: %s" % (self.comment, get_classname(self.range))

    def __get__(self, instance, instance_type):
        if instance is None:
            return self

        uri = instance.uri
        if uri.startswith("http://"):
            uri = "<%s>" % uri

        results = tracker.SparqlQuery("SELECT ?v WHERE { %s %s ?v }" % (uri, self.uri))
        for result in results:
            #FIXME: What to do about lists of stuff. What to do about stuff that isnt a string.
            result = result[0]
            if self.uri == "rdfs:range":
                return str(result)
            else:
                return types.get_class(self.range)(result)

    def __set__(self, instance, value):
        if instance is None:
            return
        if isinstance(value, Resource):
            if value.uri.startswith("http://"):
                instance.triples[self.uri] = "<%s>" % value.uri
            else:
                instance.triples[self.uri] = value.uri
        else:
            instance.triples[self.uri] = '"%s"' % value

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

        self.wrapped["xsd:boolean"] = lambda x: x=='true'
        self.wrapped["xsd:integer"] = int
        self.wrapped["xsd:double"] = float
        self.wrapped["rdfs:Literal"] = str
        self.wrapped["xsd:string"] = str
        self.wrapped['xsd:date'] = str
        self.wrapped['xsd:dateTime'] = str

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
            baseclass = [self.get_class(baseclass.uri)]
        else:
            baseclass = [Resource]

        # Does this class have notifications?
        if cls.notify:
            attrs['notifications'] = Notifications(cls.uri)

        # Enumerate all properties of this class
        for prop in Property.get(domain=cls.uri):
            if prop.label:
                attrs[prop.label.lower().replace(" ", "_")] = prop

        # Make a new class
        klass = type(str(classname), tuple(baseclass), attrs)

        # Cache it for later
        self.wrapped[klass._type_] = klass

        return klass

types = WrapperFactory()

if __name__ == "__main__":
    #help(w.get_class("rdfs:Resource"))
    #help(w.get_class("rdfs:Class"))
    self = __import__(__name__)
    for cls in Class.get():
        cls = types.get_class(cls.uri)
        setattr(self, cls.__name__, cls)
    help(self)

    foo = {}
    for p in Property.get():
        foo.setdefault(p.range, 0)
        foo[p.range] += 1

    for k, v in foo.items():
        print k, v

