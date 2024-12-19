from pylive.utils.unique import make_unique_id, make_unique_name

import unittest


class TestUniqueName(unittest.TestCase):
    def test_unique_name(self):
        unique_name = make_unique_name("name", [])
        self.assertEqual(unique_name, "name")

        unique_name = make_unique_name("name", ["name"])
        self.assertEqual(unique_name, "name1")

        unique_name = make_unique_name("name", ["name1"])
        self.assertEqual(unique_name, "name")

        unique_name = make_unique_name("name", ["name", "name1"])
        self.assertEqual(unique_name, "name2")

    # def test_force_digits(self):
    #     unique_name = make_unique_name("name", [], force_digits=True)
    #     self.assertEqual(unique_name, ["name1"])

    #     unique_name = make_unique_name("name", ["name"], force_digits=True)
    #     self.assertEqual(unique_name, "name1")

    #     unique_name = make_unique_name("name", ["name1"], force_digits=True)
    #     self.assertEqual(unique_name, "name2")


if __name__ == "__main__":
    unittest.main()
