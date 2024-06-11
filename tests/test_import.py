from unittest import TestCase

class TestImport(TestCase):
    def test_import(self):
        """Test if the function get_xml can be imported from the package. I.e. package was installed correctly."""
        from sila2_feature_lib import get_xml