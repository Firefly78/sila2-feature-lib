# Simulation Feature (V1.0)

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio
from unitelabs.cdk import Connector

from sila2_feature_lib.simulation.v001_0.feature_ul import SimulatorController
from sila2_feature_lib.simulation.v001_0.feature_ul import SimulationModeGlobal as SimMode

# Create SiLA server
app = Connector({...})

# Create feature
sim_feature = SimulatorController()

# Add feature to SiLA server
app.register(sim_feature)

# Start server
asyncio.get_event_loop().run_until_complete(app.start())

# Then the following code is used to get/set the simulation mode
# Check if in simulation mode
SimMode.is_simulation_active() # Singletonian access

# Active simulation mode
SimMode.set_simulation_active()

# Deactivate simulation mode
SimMode.set_simulation_inactive()

# Also possible to register callbacks for simulation mode changes
SimMode.register_on_change(lambda new_state: print(f"Simulation mode changed to {new_state}"))

```
