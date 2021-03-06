#! /usr/bin/env python
# test.py
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

import unittest
import uuid
import datetime

import tralchemy

class TestNamespaces(unittest.TestCase):

    def test_import(self):
        """ Should be able to import a module for a namespace """
        from types import ModuleType
        from tralchemy import rdf
        self.failUnless(isinstance(rdf, ModuleType))
        import tralchemy.rdfs
        self.failUnless(isinstance(tralchemy.rdfs, ModuleType))

    def test_import_fail(self):
        """ Should get an ImportError if there is no such name space """
        self.failUnlessRaises(ImportError, __import__, "tralchemy.no_such_ontology")
        self.failUnlessRaises(ImportError, __import__, "tralchemy.no.nested.ontologies")


class TestClasses(unittest.TestCase):

    def test_make_class(self):
        """ Should be able to get an object representing a class in the ontologies """
        from tralchemy.nid3 import ID3Audio
        self.failIfEqual(ID3Audio, None)
        self.failUnless('title' in dir(ID3Audio))

    def test_instance_class(self):
        """ Should be able to make an instance of a class from the ontologies """
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")

    def test_pydoc_classname(self):
        """ pydoc should name the classes appropriately """
        import pydoc
        from tralchemy.rdfs import Class
        self.failUnlessEqual(pydoc.classname(Class, "tralchemy.rdfs"), "Class")
        self.failUnlessEqual(pydoc.classname(Class, "tralchemy.rdf"), "tralchemy.rdfs.Class")

    def test_help(self):
        """ Make sure classes have docstrings """
        from tralchemy.nid3 import ID3Audio
        self.failIfEqual(ID3Audio.__doc__, None)


class TestProperty(unittest.TestCase):

    def test_get(self):
        """ Should be able to get properties """
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")
        a = obj.modified

    def test_set(self):
        """ Should be able to set properties """
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")
        obj.notify = True

    def test_help(self):
        """ Poke help """
        from tralchemy.nid3 import ID3Audio
        self.failIfEqual(ID3Audio.leadArtist.__doc__, None)

    def test_types_string(self):
        """ Test types of properties """
        from tralchemy.xsd import string
        # If we ask wrapper for a string, we should get a string type
        self.failUnlessEqual(string, str)

        from tralchemy.nid3 import ID3Audio
        # cls1 is a class, so accessing properties on it will return self rather then actually doing anything in __get__
        self.failUnlessEqual(type(ID3Audio.leadArtist), tralchemy.core.Property)
        # But now we are access the contents of artist, which is an instance, so it runs __get__ and should return a comment
        self.failUnlessEqual(type(ID3Audio.leadArtist.comment), str)


class TestRecords(unittest.TestCase):

    def test_inject_feed(self):
        """ Should be able to commit objects """
        from tralchemy.nmo import FeedMessage
        feedmsg = FeedMessage("http://localhost/feed/%s" % str(uuid.uuid4()))
        today = datetime.datetime.today()
        date = today.isoformat() + "+00:00"

        feedmsg.contentlastmodified = date
        feedmsg.communicationchannel = "http://planet.gnome.org/atom.xml"
        feedmsg.title = "Your face"
        feedmsg.commit()

    def test_delete(self):
        """ Should be able to delete objects """
        from tralchemy.nmo import FeedMessage
        self.test_inject_feed()
        a = 0
        for msg in FeedMessage.get():
            a += 1
            msg.delete()
        self.failUnless(a > 0)
        b = 0
        for msg in FeedMessage.get():
            b += 1
        self.failUnlessEqual(b, 0)

    def test_get_with_criteria(self):
        """ Should be able to fetch a subset of the store objects """
        from tralchemy.rdfs import Class
        self.failUnless(len(list(Class.get())) > len(list(Class.get(notify="true"))))


class TestPropertyList(unittest.TestCase):

    def test_len(self):
        """ Should be able to get the length of a list property """
        from tralchemy.rdfs import Class
        foo = Class("nco:PersonContact")
        self.failUnlessEqual(len(foo.subClassOf), 1)
        foo = Class("ncal:Event")
        self.failUnlessEqual(len(foo.subClassOf), 2)

    def test_append(self):
        """ Should be able to append to a lst property """
        from tralchemy.nco import PersonContact, PhoneNumber
        p = PersonContact.create(commit=False)
        for i in range(5):
            pn = PhoneNumber.create(phoneNumber=str(i))
            p.hasPhoneNumber.append(pn)
        p.commit()
        self.failUnlessEqual(len(p.hasPhoneNumber), 5)
        return p.uri

    def test_list(self):
        """ Should be able to retrieve a list from a property """
        uri = self.test_append()
        from tralchemy.nco import PersonContact
        p = PersonContact(uri)
        i = 0
        k = 0
        for j in p.hasPhoneNumber:
            i += 1
            k += int(j.phoneNumber)
        self.failUnlessEqual(i, 5)
        self.failUnlessEqual(k, (4+3+2+1+0))

    def test_dont_assign_to_list(self):
        """ Don't support directly assigning to a list property """
        #FIXME: In the future, you might be able to accept a list/set/tuple, and this test will
        # need to be relaxed
        from tralchemy.rdfs import Class
        cls = Class("rdfs:Class")
        self.failUnlessRaises(ValueError, setattr, cls, "subClassOf", "yourface")


if __name__ == '__main__':
    unittest.main()
