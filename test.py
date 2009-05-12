#! /usr/bin/env python

import tralchemy
import unittest
import uuid
import datetime

class TralchemyTests(unittest.TestCase):

    def setUp(self):
        self.wrapper = tralchemy.WrapperFactory()

    def test_make_class(self):
        cls = self.wrapper.get_class("nid3:ID3Audio")
        assert cls != None
        assert 'title' in dir(cls)

    def test_instance_class(self):
        cls = self.wrapper.get_class("rdfs:Class")
        obj = cls("nid3:ID3Audio")

    def test_get_property(self):
        cls = self.wrapper.get_class("rdfs:Class")
        obj = cls("nid3:ID3Audio")
        print obj.subclassof

    def test_set_property(self):
        cls = self.wrapper.get_class("rdfs:Class")
        obj = cls("nid3:ID3Audio")
        obj.subclassof = "badger"

    def test_property_help(self):
        cls = self.wrapper.get_class("nid3:ID3Audio")
        assert cls.__doc__ != None
        assert cls.artist != None

    def test_property_types_string(self):
        cls2 = self.wrapper.get_class("xsd:string")
        # If we ask wrapper for a string, we should get a string type
        assert cls2 == str, "Got %s" % type(cls2)

        cls1 = self.wrapper.get_class("nid3:ID3Audio")
        # cls1 is a class, so accessing properties on it will return self rather then actually doing anything in __get__
        assert type(cls1.artist) == tralchemy.Property, "Got %s" % type(cls1.artist)
        # But now we are access the contents of artist, which is an instance, so it runs __get__ and should return a comment
        assert type(cls1.artist.comment) == str, "Got %s" % type(cls1.artist.comment)

    def test_inject_feed(self):
        feedmsgcls = self.wrapper.get_class("nmo:FeedMessage")
        feedmsg = feedmsgcls("http://localhost/feed/%s" % str(uuid.uuid4()))
        today = datetime.datetime.today()
        date = today.isoformat() + "+00:00"

        feedmsg.contentlastmodified = date
        feedmsg.communicationchannel = "http://planet.gnome.org/atom.xml"
        feedmsg.title = "Your face"
        feedmsg.commit()

    def test_delete(self):
        FeedMessage = self.wrapper.get_class("nmo:FeedMessage")
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

    def test_get_with_criteria(self):
        Class = self.wrapper.get_class("rdfs:Class")
        assert len(list(Class.get())) > len(list(Class.get(notify="true")))

if __name__ == '__main__':
    unittest.main()
