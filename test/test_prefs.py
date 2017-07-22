from src.prefs import *
import unittest

class TestPreferences(unittest.TestCase):
    def test_make_key(self):
        self.assertEqual(make_key(None), tuple())
        self.assertEqual(make_key((1,)), (1,))
        self.assertEqual(make_key(1), (1,))
        self.assertEqual(make_key([1,2,3]), (1,2,3))

    def test_get_preference(self):
        d = {(0,): "foo", (0,1): "bar"}
        prefs = Preferences(d)

        self.assertEqual(prefs.get_preference((0,1,2)), "bar")
        self.assertEqual(prefs.get_preference((0,1)), "bar")
        self.assertEqual(prefs.get_preference((0,2)), "foo")

        with self.assertRaises(ValueError):
            prefs.get_preference((1,))
        with self.assertRaises(ValueError):
            prefs.get_preference(None)

        d[tuple()] = "baz"
        prefs = Preferences(d)

        self.assertEqual(prefs.get_preference((1,)), "baz")
        self.assertEqual(prefs.get_preference(None), "baz")

    def test_set_preference(self):
        d = {(0,): "foo", (0,1): "bar"}
        prefs = Preferences(d)

        prefs.set_preference((0,1,2), "baz")
        self.assertEqual(prefs.get_preference((0,1,2)), "baz")

        prefs.set_preference((0,), "eggs")
        self.assertEqual(prefs.get_preference((0,)), "eggs")
        self.assertEqual(prefs.get_preference((0,1)), "bar")

        prefs.set_preference((0,), "ham", override_subprefs=True)
        self.assertEqual(prefs.get_preference((0,)), "ham")
        self.assertEqual(prefs.get_preference((0,1)), "ham")
        self.assertEqual(prefs.get_preference((0,1,2)), "ham")    