"""
Test serialization in json format
"""
import unittest
from entity.Player import Player

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
        """
        Test serialization of Map entity to json string
        """
        pass
    
    def test_player(self):
        """
        Test Player entity serialization/deserialization
        """
        player1 = Player('vasya')
        str_data = player1.to_json_str()
        player2 = Player('')
        player2.from_json_str(str_data)
        self.assertEqual(player1.name, player2.name)
        self.assertEqual(player1.id, player2.id)

        a = Player('Gadya')
        b = Player('Gadya')
        self.assertEqual(a.id, b.id)
        



if __name__ == '__main__':
    unittest.main()
