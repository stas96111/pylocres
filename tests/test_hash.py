import unittest
from pylocres.city_hash import CityHash

class TestHashing(unittest.TestCase):
    
    def test_hash_values(self):
        
        test_cases = [
            ('', 0), 
            ('I', 366061642),
            ('HI', 4113122066),
            ("List", 2316514818),
            ("Tests Tests", 2426432524),
            ("a" * 17, 3926091141),
            ("Test" * 20, 3317857492),
        ]
        
        for value, expected_hash in test_cases:
            result = CityHash.city_hash_64_utf16_to_uint32(value)
            self.assertEqual(result, expected_hash, f"Failed for value: {value}")

if __name__ == '__main__':
    unittest.main()