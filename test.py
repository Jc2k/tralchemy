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

if __name__ == '__main__':
    unittest.main()
