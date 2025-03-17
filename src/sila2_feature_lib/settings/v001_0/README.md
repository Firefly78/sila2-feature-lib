# Settings Feature (V1.0)

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio
from unitelabs.cdk import Connector

<<<<<<< HEAD
from sila2_feature_lib.settings.v001_0.feature_ul import SettingsService, DataStore
=======
from sila2_feature_lib.settings.v001_0.feature_ul import SettingsService, access_data_store, DataStore
>>>>>>> ade79cdc577575ffeec64b54ccf732fda3f80983

# Create SiLA server
app = Connector({...})

# Implement custom data store that tracks key/valus on-drive
class OnDriveStore(DataStore):
    def __init__(
        self,
        *,
        url: Union[str, Path],
        **kwargs,
    ):
        self.url = Path(url)
        self.url.touch(exist_ok=True)

        data = self._load()

        super().__init__(**kwargs)
        self._content = data  # Override content

    def register(self, key: str, value: Any):
        super().register(key, value)
        self._save()

    def reload(self):
        self._content = self._load()
        self.callbacks.trigger(self, event="on_reload")

    def update(self, key: str, value: Any):
        super().update(key, value)
        self._save()

    def _save(self):
        with open(self.url, "w") as f:
            yaml.safe_dump(self._content, f, indent=2)

    def _load(self):
        with open(self.url, "r") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise TypeError("Root object must be a dictionary", {self.url})

        return data


# Create feature using our custom store
settings = SettingsService(store=OnDriveStore())

# Add feature to SiLA server
app.register(data_feature)

# Start server
asyncio.get_event_loop().run_until_complete(app.start())

```

### From anywhere else in you application

```python
<<<<<<< HEAD
from sila2_feature_lib.settings.v001_0.feature_ul import access_data_store

=======
>>>>>>> ade79cdc577575ffeec64b54ccf732fda3f80983
# Get acces to store
store : OnDriveStore = access_data_store()
# Add things to store (any json - serializable object, more or less)
store.register("my_settings", {"url": "localhost", "port": 50002})
# Read back
port = store.register("my_settings.port")
# Or subscribe to changes
store.callbacks.on_update(lambda db, k, v: print(f"{k} => {str(v)}"))
<<<<<<< HEAD

=======
>>>>>>> ade79cdc577575ffeec64b54ccf732fda3f80983
```
