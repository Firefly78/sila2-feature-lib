# SiLA2 Feature Library

## Introduction

This library provides a set of SiLA2 feature templates that can be used to create SiLA2-compliant devices.
It fills two use cases:

1. Make it simple to add features to any SiLA server, with standard implementations that does what you want in 90% of the cases. :)
2. Or just get the feature definition and implement it yourself.

## Example

Example using the unitelabs framework.

Install sila2-feature-library, with the `unitelabs` dependency.

```bash
$ pip install sila2-feature-lib[unitelabs]
```

Import and add a feature from the library to your SiLA server.

```python
from unitelabs import Connector
from sila2_feature_lib.simulation.v001_0.feature_ul import SimulatorController

# Create SiLA server
app = Connector({...})

# Append feature to SiLA server
app.register(SimulatorController())

# Run server
asyncio.get_event_loop().run_until_complete(app.start())
```

That's it. You now have a running SiLA server with the default implementation of the `SimulatorController` feature running.

## Library Structure

TBD
