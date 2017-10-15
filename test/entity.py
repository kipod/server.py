"""
Test server entities
"""
import unittest
from server.entity.Map import Map

class TestJsonSerializable(unittest.TestCase):
    """
    Test-fixture
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip("demo - simple testcase")
    def test_upper(self):
        """ simple tast case """
        self.assertEqual('foo'.upper(), 'FOO')

    def test_map(self):
        """ test create map entity """
        map01 = Map("map01")
        self.assertTrue(map01.okey)
        self.assertEqual(len(map01.line), 12)
        self.assertEqual(len(map01.point), 12)
