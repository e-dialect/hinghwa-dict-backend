import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from src.matcher.precise_ipa_matcher import PreciseIPAMatcher

class TestPreciseIPAMatch(unittest.TestCase):
    def setUp(self):
        self.matcher = PreciseIPAMatcher()

    def test_precise_match_ayi(self):
        test_ipa = "pa42lau21"
        print(f"\n测试IPA：{repr(test_ipa)}")
        
        res = self.matcher.precise_ipa_match(test_ipa)
        
        print(f"匹配结果：{res}")

if __name__ == "__main__":
    unittest.main()