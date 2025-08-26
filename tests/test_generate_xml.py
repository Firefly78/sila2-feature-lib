from unittest import TestCase

from sila2_feature_lib.scripts.generate_xml import xml_from_feature
from sila2_feature_lib.simulation.v001_0.feature_ul import SimulatorController


class TestGenerateXML(TestCase):
    def test_generate_xml_from_features(self):
        xml = xml_from_feature(SimulatorController())

        self.assertIsNotNone(xml)
        self.assertGreater(len(xml), 0)
