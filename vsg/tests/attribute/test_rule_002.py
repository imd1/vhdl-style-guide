
import unittest

from vsg.rules import attribute


class test_rule(unittest.TestCase):

    def test_rule_002(self):
        oRule = attribute.rule_002()
        self.assertTrue(oRule)
        self.assertEqual(oRule.name, 'attribute')
        self.assertEqual(oRule.identifier, '002')
        self.assertTrue(oRule.depricated)
