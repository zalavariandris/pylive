import unittest
from typing import *
from pylive.utils.diff import Change, diff_dict, diff_list, patch_list, patch_dict

class TestDiff(unittest.TestCase):
	def test_dictdiff(self):
		# Example usage
		dict_a = {"a": 1, "b": 2, "c": 3}
		dict_b = {"b": 2, "c": 4, "d": 5}

		diff = diff_dict(dict_a, dict_b)

		self.assertEqual(diff, Change(
			added    ={'d': 5},
			removed  ={'a': 1},
			changed  ={'c': (3, 4)},
			unchanged={'b': 2}
		))
	
	def test_listdiff(self):
		list_a = [1, 2, 3, 4]
		list_b = [1, 3, 5, 4, 6]

		diff = diff_list(list_a, list_b)
		
		self.assertEqual(diff, Change(
			added={1: 3, 2: 5, 4: 6}, 
			removed={1: 2, 2: 3}, 
			changed={}, 
			unchanged={0: 1, 3: 4}
		))

class TestPatch(unittest.TestCase):
	def test_dictpatch(self):
		# Example usage
		dict_a = {"a": 1, "b": 2, "c": 3}
		dict_b = {"b": 2, "c": 4, "d": 5}

		diff = diff_dict(dict_a, dict_b)

		updated = patch_dict(dict_a, diff)

		self.assertEqual(dict_b, updated)
	
	def test_listpatch(self):
		list_a = [1, 2, 3, 4]
		list_b = [1, 3, 5, 4, 6]

		diff = diff_list(list_a, list_b)
		
		updated = patch_list(list_a, diff)
		self.assertEqual(list_b, updated)

if __name__ == "__main__":
	unittest.main()