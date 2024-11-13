# DataStore Feature (V1.0)

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio
from unitelabs.cdk import Connector

from sila2_feature_lib.datastore.v001_0.feature_ul import DataStoreService
from sila2_feature_lib.datastore.v001_0.feature_ul.extras.resource_handle import ResourceHandle

# Create SiLA server
app = Connector({...})

# Defined connection type
handle = ResourceHandle(url="http://localhost:8080")

# Create feature
data_feature = DataStoreService[ResourceHandle](handle=handle)

# Add feature to SiLA server
app.register(data_feature)

# Start server
asyncio.get_event_loop().run_until_complete(app.start())

# Access the connection from anywhere in the code
with DataStoreService[ResourceHandle].get_handle() as h:
    await h.test()

```
