# Settings Feature (V1.0)

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio

import yaml
from unitelabs.cdk import Connector

from sila2_feature_lib.settings.v001_0.feature_ul import OnDriveStore, SettingsService

# Create SiLA server
app = Connector({...})

# Create feature with our settings stored on-drive
my_store = OnDriveStore(
    url=".my_settings.json", serialize=yaml.dump, deserialize=yaml.unsafe_load
)
settings = SettingsService(store=my_store)

# Add feature to SiLA server
app.register(settings)

# Start server
asyncio.get_event_loop().run_until_complete(app.start())
```

### From anywhere else in you SiLA application

```python
from sila2_feature_lib.settings.v001_0.feature_ul import access_data_store

# Get acces to store
store = access_data_store()
# Add things to store (any json - serializable object, more or less)
store.register("my_settings", {"url": "localhost", "port": 50002})
# Read back
port = store.read("my_settings.port")
# Or subscribe to changes
store.callbacks.on_update.append(lambda db, k, v: print(f"{k} => {str(v)}"))
```

### Finally

Settings are also accessible (read/write) by default through the `SettingsService` SiLA feature.
