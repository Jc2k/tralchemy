#! /usr/bin/env python

import unittest
import uuid
import datetime

import tralchemy

class TestClasses(unittest.TestCase):

    def test_make_class(self):
        from tralchemy.nid3 import ID3Audio
        self.failIfEqual(ID3Audio, None)
        self.failUnless('title' in dir(ID3Audio))

    def test_instance_class(self):
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")

    def test_pydoc_classname(self):
        import pydoc
        from tralchemy.rdfs import Class
        self.failUnlessEqual(pydoc.classname(Class, "tralchemy.rdfs"), "Class")
        self.failUnlessEqual(pydoc.classname(Class, "tralchemy.rdf"), "tralchemy.rdfs.Class")

class TestProperty(unittest.TestCase):

    def test_get(self):
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")
        self.failUnlessEqual(len(obj.subClassOf), 1)

    def test_set(self):
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")
        obj.subClassOf = "badger"

    def test_help(self):
        from tralchemy.nid3 import ID3Audio
        self.failIfEqual(ID3Audio.__doc__, None)
        self.failIfEqual(ID3Audio.leadArtist, None)

    def test_types_string(self):
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
        from tralchemy.nmo import FeedMessage
        feedmsg = FeedMessage("http://localhost/feed/%s" % str(uuid.uuid4()))
        today = datetime.datetime.today()
        date = today.isoformat() + "+00:00"

        feedmsg.contentlastmodified = date
        feedmsg.communicationchannel = "http://planet.gnome.org/atom.xml"
        feedmsg.title = "Your face"
        feedmsg.commit()

    def test_delete(self):
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
        from tralchemy.rdfs import Class
        self.failUnless(len(list(Class.get())) > len(list(Class.get(notify="true"))))


class TestPropertyList(unittest.TestCase):

    def test_len(self):
        from tralchemy.rdfs import Class
        foo = Class("nco:PersonContact")
        self.failUnlessEqual(len(foo.subClassOf), 1)
        foo = Class("ncal:Event")
        self.failUnlessEqual(len(foo.subClassOf), 2)

    def test_append(self):
        from tralchemy.nco import PersonContact, PhoneNumber
        p = PersonContact.create(commit=False)
        for i in range(5):
            pn = PhoneNumber.create(phoneNumber=str(i))
            p.hasPhoneNumber.append(pn)
        p.commit()
        self.failUnlessEqual(len(p.hasPhoneNumber), 5)
        return p.uri

    def test_list(self):
        uri = self.test_append()
        from tralchemy.nco import PersonContact
        p = PersonContact(uri)
        i = 0
        k = 0
        for j in p.hasPhoneNumber:
            i += 1
            k += int(j.phoneNumber)
        self.failUnlessEqual(i, 5)
        self.failUnlessEqual(k, (5+4+3+2+1))


if __name__ == '__main__':
    unittest.main()
