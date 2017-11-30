""" Test server entities.
"""
import json
import unittest

from server.entity.Map import Map


class TestJsonSerializable(unittest.TestCase):
    """ Test-fixture.
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skip("Demo - simple test case")
    def test_upper(self):
        """ Simple test case.
        """
        self.assertEqual('foo'.upper(), 'FOO')

    def test_map(self):
        """ Test create map entity.
        """
        map02 = Map('map02')
        self.assertTrue(map02.okey)
        self.assertEqual(len(map02.line), 18)
        self.assertEqual(len(map02.point), 12)

    def test_dump_map(self):
        """ Test JSON conversion.
        """
        m = Map('map02')
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
        self.assertNotIn('train', data)
        self.assertNotIn('size', data)
        self.assertNotIn('coordinate', data)

        str_json = m.layer_to_json_str(1)
        data = json.loads(str_json)
        self.assertNotIn('name', data)
        self.assertNotIn('line', data)
        self.assertNotIn('point', data)
        self.assertNotIn('size', data)
        self.assertNotIn('coordinate', data)
        self.assertIn('idx', data)
        self.assertIn('post', data)
        self.assertIn('train', data)

        str_json = m.layer_to_json_str(10)
        data = json.loads(str_json)
        self.assertNotIn('name', data)
        self.assertNotIn('line', data)
        self.assertNotIn('point', data)
        self.assertNotIn('post', data)
        self.assertNotIn('train', data)
        self.assertIn('idx', data)
        self.assertIn('size', data)
        self.assertIn('coordinate', data)
