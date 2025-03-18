import unittest
from pylocres.city_hash import CityHash
from pylocres.crc_hash import str_crc32

class TestHashing(unittest.TestCase):
    
    def test_city_hash_values(self):
        
        test_cases = [
            ("", 0), 
            ("I", 366061642),
            ("HI", 4113122066),
            ("List", 2316514818),
            ("Tests Tests", 2426432524),
            ("a" * 17, 3926091141),
            ("Test" * 20, 3317857492),
        ]
        
        for value, expected_hash in test_cases:
            result = CityHash.city_hash_64_utf16_to_uint32(value)
            self.assertEqual(result, expected_hash, f"Failed for value: {value}")
            
    def test_crc_hash_values(self):
        
        test_cases = [
            ('Test crc', 2908429949), 
            ("Locres", 1425315323),
            ('A' * 100, 2416283133),
            ('ABC' * 100, 426380042),
        ]
        
        for value, expected_hash in test_cases:
            result = str_crc32(value)
            self.assertEqual(result, expected_hash, f"Failed for value: {value}")

# python -m unittest discover -s tests

if __name__ == '__main__':
    unittest.main()