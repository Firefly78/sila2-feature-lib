from unitelabs.cdk import Connector

from sila2_feature_lib import dynamic_import, dynamic_import_config

# Dynamically import a feature for your driver
app = Connector({...})
target = "user_provided_feature:feature1"
feat = dynamic_import(target)

app.register(feat())  # Initialize the feature and register it with the app


# Dynamically import any number of features from a configuration file
app = Connector({...})
config = "path/to/config.json"
features = dynamic_import_config(config)

for feature in features:
    # Register each feature with the app
    app.register(feature)
