from unittest import TestCase

from sila2_feature_lib import dynamic_import, dynamic_import_config


class TestDynamicImport(TestCase):
    def test_dynamic_import(self):
        """Test dynamic import"""
        f = dynamic_import("resources.import_me:func1")
        self.assertEqual(f.__name__, "func1")

    def test_dynamic_import_config(self):
        """Test dynamic import config"""
        items = dynamic_import_config("tests/resources/import_config.json")
        self.assertEqual(len(items), 1)  # On item in the config file
        self.assertEqual(type(items[0]).__name__, "MyClass")  # Name match
        self.assertEqual(items[0].args, (1, 2, 3))
        self.assertEqual(items[0].kwargs, {"a": 1, "b": 2})
