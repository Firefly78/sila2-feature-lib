# Resource Feature (V1.0)

## Description
Feature for handling a series of external connections, other SiLA servers, rest APIs, etc.
It loads a configuration file with the resources and creates a global resource object that can be used to call the resources. Via the SiLA feature one can also view the status of the resources (OK/NOK).

## Example usage (Unitelabs SiLA2 framework)

# Add feature to a SiLA server (unitelabs):
```python
import asyncio
from unitelabs.cdk import Connector
from sila2_feature_lib.resource.v001_0.feature_ul import ResourcesService

# Create SiLA server
app = Connector({...})

# Create feature
feature = ResourcesService(config="config.yaml")

# Add feature to SiLA server
app.register(feature)

# Start server
asyncio.get_event_loop().run_until_complete(app.start())
```

config.yaml:
```yaml
resources:
  my_driver_1:
    alias: mydriver.1
    url: 192.168.1.1:50001
    type: sila2
    sim: false # Simulation mode
  my_second_driver:
    ...
```


Then the following code is used from the other features of your SiLA server to access the global resources
```python
from sila2_feature_lib.resource.v001_0.feature_ul import GlobalResources as GR
from sila2_feature_lib.resource.v001_0.util.communication import sila_call_cash

# Get a handle of a function used to call the resource
f = GR.GetHandle("mydriver.1")

# Call the resource
rpl = await f(method="MyFeature.Command1", arg1, arg2)

# Optionally, use call_cash to share SilaClient between calls (faster)
with sila_call_cash():
    rpl = await f(method="MyFeature.Command1", arg1, arg2)
    rpl = await f(method="MyFeature.Command2", arg1, arg2)
    rpl = await f(method="MyFeature.Command3", arg1, arg2)
```

Supports registering custom resource types
```python
from sila2_feature_lib.resource.v001_0.feature_ul import GlobalResources as GR
from sila2_feature_lib.resource.v001_0.util.communication import BaseCall

# Make your own custom resource type
class SerialCall(BaseCall):
  async def Call(self, *args, **kwargs):
    with Serial(self.url) as serial:
      serial.write(self.method)
      return serial.read()

  async def Ping(self):
    with Serial(self.url) as serial:
      serial.write("ping")
      return serial.read() == "pong"

GR.RegisterResourceType("serialport", SerialCall)
```
