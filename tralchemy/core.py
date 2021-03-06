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

import dateutil.parser

bus = dbus.SessionBus()
tracker_obj = bus.get_object("org.freedesktop.Tracker", "/org/freedesktop/Tracker/Resources")
tracker = dbus.Interface(tracker_obj, "org.freedesktop.Tracker.Resources")

def tracker_query(sparql):
    sparql = sparql.replace('\n', '\\n')
    return tracker.SparqlQuery(sparql)

def tracker_update(sparql):
    sparql = sparql.replace('\n', '\\n')
    return tracker.SparqlUpdate(sparql)

# Map tracker prefixes to ontology namespaces and back
namespaces = {}
for prefix, namespace in tracker_query("SELECT ?prefix, ?ns WHERE { ?ns tracker:prefix ?prefix }"):
    namespaces[namespace] = prefix
del prefix, namespace

def get_classname(classname):
    """ Takes a classname and flattens it into tracker form """
    if classname.startswith("http://"):
        for ns, prefix in namespaces.iteritems():
            if classname.startswith(ns):
                return prefix + ":" + classname[len(ns):]
    return classname


class Notifications(object):
    """ Class to allow users to attach signals to a class of object """
    def __init__(self, uri, signal):
        self.uri = uri.replace(":", "/")
        self.signal = signal

    def subscribe(self, callback):
        def _(subjects):
            subjects = [str(subject) for subject in subjects]
            return callback(subjects)
        bus.add_signal_receiver (_, signal_name=self.signal,
                                 dbus_interface="org.freedesktop.Tracker.Resources.Class",
                                 path="/org/freedesktop/Tracker/Resources/Classes/%s" % self.uri)


class Resource(object):
    """ Everything is a resource """

    _type_ = "rdfs:Resource"
    __module__ = "tralchemy.rdfs"

    def __init__(self, uri):
        self.uri = get_classname(uri)
        self.triples = {}
        self.cache = {}

    def properties(self):
        uri = self.uri
        if uri.startswith("http://"):
            uri = "<%s>" % uri
        results = tracker_query("SELECT ?key, ?value WHERE { %s ?key ?value }" % uri)
        for key, value in results:
            yield get_classname(str(key)), str(value)

    @classmethod
    def get(cls, **kwargs):
        fragment = ""
        for key, value in kwargs.iteritems():
            key = getattr(cls, key).uri
            fragment += " . ?o %s %s" % (key, value)

        results = tracker_query("SELECT ?o WHERE { ?o rdf:type %s %s}" % (cls._type_, fragment))
        for result in results:
            classname = get_classname(result[0])
            yield cls(classname)

    @classmethod
    def create(cls, **kwargs):
        o = cls(kwargs.get('uid', 'http://localhost/resource/%s' % str(uuid.uuid4())))
        for k, v in kwargs.iteritems():
            if k == "uid" or k =="commit":
                continue
            setattr(o, k, v)
        if not 'commit' in kwargs or kwargs['commit']:
            o.commit()
        return o

    def delete(self):
        #tracker_update("DELETE { <%s> ?p ?o }" % self.uri)
        tracker_update("DELETE { <%s> a %s. }" % (self.uri, self._type_))

    def commit(self):
        query = "INSERT { <%s> a %s" % (self.uri, self._type_)
        for k, v in self.triples.iteritems():
            if isinstance(v, list):
                for i in v:
                    query += " ; %s %s" % (k, i)
            else:
                query += " ; %s %s" % (k, v)
        query += " . }"
        tracker_update(query)
        self.triples = {}


class PropertyList(object):

    def __init__(self, uri, range, instance):
        self.uri = uri
        self._range_ = range
        self.instance = instance
        self.vals = []

        instance_uri = instance.uri
        if instance_uri.startswith("http://"):
            instance_uri = "<%s>" % instance_uri

        # Get all items of this type
        for result in tracker_query("SELECT ?o WHERE { %s %s ?o }" % (instance_uri, uri)):
            result = result[0]
            self.vals.append(types.get_class(range)(result))

    def append(self, value):
        if isinstance(value, Resource):
            if value.uri.startswith("http://"):
                eval = "<%s>" % value.uri
            else:
                eval = value.uri
        else:
            eval = '"%s"' % value

        self.instance.triples.setdefault(self.uri, []).append(eval)
        self.vals.append(value)

    def __delitem__(self, idx):
        raise NotImplementedError

    def __setitem__(self, idx, value):
        raise NotImplementedError

    def __getitem__(self, idx):
        return self.vals[idx]

    def __len__(self):
        return len(self.vals)

    def __iter__(self):
        return iter(self.vals)

    def __repr__(self):
        return repr(self.vals)

    def __str__(self):
        return str(self.vals)


class Property(Resource, property):

    _type_ = "rdf:Property"
    __module__ = "tralchemy.rdf"

    def __init__(self, uri):
        super(Property, self).__init__(uri)

        sparql = "SELECT ?max ?range ?comment WHERE { " \
                     "%s a rdf:Property . " \
                     "OPTIONAL { %s nrl:maxCardinality ?max } . " \
                     "OPTIONAL { %s rdfs:range ?range } . " \
                     "OPTIONAL { %s rdfs:comment ?comment } " \
                 "}"

        results = tracker_query(sparql % (uri, uri, uri, uri))
        for result in results:
            self._maxcard_ = int(result[0]) if result[0] else None
            self._range_ = result[1]
            self.__doc__ = "%s\n\n@type: %s" % (result[2], get_classname(self._range_))

    def is_list(self):
        return not self._maxcard_ or self._maxcard_ > 1

    def __get__(self, instance, instance_type):
        if instance is None:
            return self

        # Just so pychecker doesnt moan
        assert instance_type

        if self.is_list():
            if not self.uri in instance.cache:
                instance.cache[self.uri] = PropertyList(self.uri, self._range_, instance)
            return instance.cache[self.uri]

        uri = instance.uri
        if uri.startswith("http://"):
            uri = "<%s>" % uri

        results = tracker_query("SELECT ?v WHERE { %s %s ?v }" % (uri, self.uri))
        for result in results:
            #FIXME: What to do about lists of stuff. What to do about stuff that isnt a string.
            result = result[0]
            if self.uri == "rdfs:range":
                return str(result)
            else:
                return types.get_class(self._range_)(result)

    def __set__(self, instance, value):
        if instance is None:
            return

        if self.is_list():
            raise ValueError("Cannot assign directly to a list property")

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
Resource.modified = Property("tracker:modified")

Property.domain = Property("rdfs:domain")
Property.subpropertyof = Property("rdfs:subPropertyOf")
Property.range = Property("rdfs:range")
Property.indexed = Property("tracker:indexed")
Property.fulltextindexed = Property("tracker:fulltextIndexed")
Property.transient = Property("tracker:transient")
Property.maxcardinality = Property("nrl:maxCardinality")


class Class(Resource):

    _type_ = "rdfs:Class"
    __module__ = "tralchemy.rdfs"

    subClassOf = Property("rdfs:subClassOf")
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
        self.wrapped['xsd:date'] = lambda x: dateutil.parser.parser().parse(x)
        self.wrapped['xsd:dateTime'] = lambda x: dateutil.parser.parser().parse(x)

    def get_class(self, classname):
        classname = get_classname(classname)

        if classname in self.wrapped:
            return self.wrapped[classname]

        ns, name = classname.split(":")

        # Look up this class in tracker
        cls = Class(classname)

        attrs = {
            "_type_": cls.uri,
            "__doc__": cls.comment or "",
            "__module__": "tralchemy.%s" % ns,
        }

        baseclass = []
        for key, value in cls.properties():
            if key == "rdfs:subClassOf":
                baseclass.append(self.get_class(value))
        if not baseclass:
            baseclass.append(Resource)

        # An ontology might well have a pointless inheritenance chain
        # For example nmo:Message(TextDocument, InformationElement) - TextDocument is already an InfoEle!
        # Lets ignore the pointless inheritance and reduce chances of MRO related fail
        filtered = []
        for j in baseclass:
            for k in baseclass:
                if j != k and issubclass(k, j):
                    break
            else:
                filtered.append(j)

        # Does this class have notifications?
        if cls.notify:
            attrs['added'] = Notifications(cls.uri, 'SubjectsAdded')
            attrs['changed'] = Notifications(cls.uri, 'SubjectsChanged')
            attrs['removed'] = Notifications(cls.uri, 'SubjectsRemoved')

        # Enumerate all properties of this class
        for prop in Property.get(domain=cls.uri):
            if len(prop.uri.split(":")) == 2:
                attrs[prop.uri.split(":")[1]] = prop
            elif len(prop.uri.split("#")) == 2:
                attrs[prop.uri.split("#")[1]] = prop
            elif prop.label:
                # shouldn't ever get here?
                attrs[prop.label.lower().replace(" ", "_")] = prop

        # Make a new class
        klass = type(str(name), tuple(filtered), attrs)

        # Cache it for later
        self.wrapped[klass._type_] = klass

        return klass

types = WrapperFactory()

