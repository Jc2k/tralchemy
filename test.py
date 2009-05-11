#! /usr/bin/env python

import tralchemy
import unittest

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


if __name__ == '__main__':
    unittest.main()
