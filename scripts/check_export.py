
import ee

PROJECT_ID = "gen-lang-client-0439006539"

ee.Initialize(project=PROJECT_ID)

tasks = ee.batch.Task.list()

for task in tasks:
    status = task.status()

    description = status.get("description", "")
    
    if "AquaSentinel_District_Rainfall" in description:
        print("\nExport task found")
        print("Description:", description)
        print("State:", status.get("state"))
        print("Error:", status.get("error_message", "None"))
        print("Task ID:", status.get("id"))
