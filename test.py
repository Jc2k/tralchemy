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
        cls = self.wrapper.get_class("nid3:ID3Audio")
        obj = cls()

    def test_get_property(self):
        cls = self.wrapper.get_class("nid3:ID3Audio")
        obj = cls()
        print obj.title

    def test_set_property(self):
        cls = self.wrapper.get_class("nid3:ID3Audio")
        obj = cls()
        obj.title = "badger"

if __name__ == '__main__':
    unittest.main()
