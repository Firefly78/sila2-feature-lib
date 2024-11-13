# Script for generating *.sila.xml files from unitelabs sila definitions
import inspect
from importlib import import_module
from pathlib import Path

from sila import fdl_parser
from unitelabs.cdk import Connector, sila


def generate_xml():
    path = Path("./src/sila2_feature_lib")
    for p in path.glob("*/*/feature_ul.py"):
        print(f"Processing {p}...")
        import_path = ".".join(p.parts[1:])[:-3]
        module = import_module(import_path)
        for k in dir(module):
            if k.startswith("__"):
                continue
            item = getattr(module, k)
            if inspect.isclass(item) and issubclass(item, sila.Feature):
                print(f"Serializing feature: {k}")
                try:
                    app = Connector()
                    feat = item()
                    app.register(feat)
                    xml = fdl_parser.serialize_feature(
                        app.sila_server.features[feat.fully_qualified_identifier]
                    )
                    # Write to file "../<feature_name>.sila.xml"
                    (p / Path(f"../{p.parts[2]}.sila.xml")).write_text(xml)
                except Exception as e:
                    Warning(f"Failed to serialize {k}: {e}")


if __name__ == "__main__":
    generate_xml()
