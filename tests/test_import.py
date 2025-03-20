import unittest


class TestXMLImport(unittest.TestCase):
    def test_xml_load(self):
        from sila2_feature_lib import get_xml, get_xml_path

        _ = get_xml, get_xml_path  # Avoid unused import warning


class TestImport(unittest.TestCase):
    def test_datastore(self):
        from sila2_feature_lib.datastore.v001_0.feature_ul import DataStoreService

        _ = DataStoreService

    def test_labwaremanipulator(self):
        from sila2_feature_lib.labwaremanipulator.v001_0.feature_ul import (
            LabwareTransferManipulatorControllerBase,
        )

        _ = LabwareTransferManipulatorControllerBase

    def test_labwaresite(self):
        from sila2_feature_lib.labwaresite.v001_0.feature_ul import (
            LabwareTransferSiteControllerBase,
        )

        _ = LabwareTransferSiteControllerBase

    def test_reportgen(self):
        from sila2_feature_lib.reportgen.v001_0.feature_ul import ReportGenController

        _ = ReportGenController

    def test_resource(self):
        from sila2_feature_lib.resource.v001_0.feature_ul import ResourcesService

        _ = ResourcesService

    def test_settings(self):
        from sila2_feature_lib.settings.v001_0.feature_ul import SettingsService

        _ = SettingsService

    def test_simulation(self):
        from sila2_feature_lib.simulation.v001_0.feature_ul import SimulatorController

        _ = SimulatorController

    def test_workflowrunner(self):
        from sila2_feature_lib.workflowrunner.v001_0.feature_ul import (
            get_workflow_feature,
        )

        _ = get_workflow_feature
