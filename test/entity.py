"""
Test server entities
"""
import unittest
import json
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

    
    def test_dump_map(self):
        """ test JSON conversion """
        m = Map("map01")
        str_json = m.to_json_str()
        data = json.loads(str_json)
        self.assertIn('name', data)
        str_json = m.layer_to_json_str(0)
        data = json.loads(str_json)
        self.assertIn('name', data)
        self.assertIn('line', data)
        self.assertIn('point', data)
        self.assertIn('idx', data)
        self.assertNotIn('post', data)
        str_json = m.layer_to_json_str(1)
        data = json.loads(str_json)
        self.assertNotIn('name', data)
        self.assertNotIn('line', data)
        self.assertNotIn('point', data)
        self.assertIn('idx', data)
        self.assertIn('post', data)
