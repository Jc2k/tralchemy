#! /usr/bin/env python

import unittest
import uuid
import datetime

import tralchemy

class TralchemyTests(unittest.TestCase):

    def test_make_class(self):
        from tralchemy.nid3 import ID3Audio
        assert ID3Audio != None
        assert 'title' in dir(ID3Audio)

    def test_instance_class(self):
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")

    def test_get_property(self):
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")
        print obj.subclassof

    def test_set_property(self):
        from tralchemy.rdfs import Class
        obj = Class("nid3:ID3Audio")
        obj.subclassof = "badger"

    def test_property_help(self):
        from tralchemy.nid3 import ID3Audio
        assert ID3Audio.__doc__ != None
        assert ID3Audio.artist != None

    def test_property_types_string(self):
        from tralchemy.xsd import string
        # If we ask wrapper for a string, we should get a string type
        assert string == str, "Got %s" % type(string)

        from tralchemy.nid3 import ID3Audio
        # cls1 is a class, so accessing properties on it will return self rather then actually doing anything in __get__
        assert type(ID3Audio.artist) == tralchemy.core.Property, "Got %s" % type(ID3Audio.artist)
        # But now we are access the contents of artist, which is an instance, so it runs __get__ and should return a comment
        assert type(ID3Audio.artist.comment) == str, "Got %s" % type(ID3Audio.artist.comment)

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
        assert a > 0
        b = 0
        for msg in FeedMessage.get():
            b += 1
        assert b == 0

    def test_insert_multiple(self):
        from tralchemy.nco import PersonContact, PhoneNumber
        p = PersonContact.create(commit=False)
        for i in range(5):
            pn = PhoneNumber.create(phonenumber=str(i))
            p.hasphonenumber.append(pn)
        p.commit()
        assert len(p.hasphonenumber) == 5, "%d != 5" % len(p.hasphonenumber)
        return p.uri

    def test_inspect_multiple(self):
        uri = self.test_insert_multiple()
        from tralchemy import PersonContact
        p = PersonContact(uri)
        i = 0
        k = 0
        for j in p.hasphonenumber:
            i += 1
            k += int(j.phonenumber)
        assert i == 5
        assert k == (5+4+3+2+1)

    def test_get_with_criteria(self):
        from tralchemy.rdfs import Class
        assert len(list(Class.get())) > len(list(Class.get(notify="true")))

    def test_query(self):
        from tralchemy.nco import PersonContact
        from tralchemy.query import Query, Store
        q = Query(PersonContact.nickname for PersonContact in Store if PersonContact.fullname == "Rob Taylor" or PersonContact.fullname == "John Carr")

class TestPropertyList(unittest.TestCase):

    def test_list(self):
        from tralchemy.rdfs import Class
        foo = Class("nco:PersonContact")
        assert len(foo.subclassof) == 1
        foo = Class("ncal:Event")
        assert len(foo.subclassof) == 2

if __name__ == '__main__':
    unittest.main()
