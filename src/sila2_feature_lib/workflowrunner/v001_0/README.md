# Workflow Runner Feature (V1.0)

## Description
Feature for running long running async workflows in a separate task. With commands for polling the status of running processes.

## Example usage (Unitelabs SiLA2 framework)

```python
import asyncio
from unitelabs import Connector

from sila2_feature_lib.workflowrunner.v001_0.feature_ul import get_workflow_feature

# Create SiLA server
app = Connector({...})

# Define workflows
async def workflow1():
    print("Workflow 1:: Started")
    await asyncio.sleep(10) # Simulate long running workflow
    print("Workflow 1:: Ended")


# Create feature
WorkflowRunner = get_workflow_feature(allowed_workflow_names=["workflow1"])

# Implement feature commands/properties
class MyWorkflowRunner(WorkflowRunner):
    async def start_new_task(self, name :str, argument_json: str):
        if name == "workflow1":
            asyncio.create_task(workflow1()) # Start the workflow in a separate task
            return name # Return the name of the started workflow
        else:
            raise ValueError(f"Unknown workflow {name}")

        return 

    ... # Implement other required commands/properties


# Add feature to SiLA server
app.register(MyWorkflowRunner())

# Start server
asyncio.get_event_loop().run_until_complete(app.start())

```


