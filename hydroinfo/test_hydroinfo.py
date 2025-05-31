import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Mock the hassapi module
class Hass:
    def __init__(self):
        self.states = {}
        self.logger = logger
    
    def log(self, message, level="INFO"):
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    def set_state(self, entity_id, state, **kwargs):
        self.states[entity_id] = {"state": state, "attributes": kwargs}
        logger.info(f"Set state for {entity_id}: {state} with attributes {kwargs}")
    
    def run_every(self, callback, start, interval):
        logger.info(f"Scheduled {callback.__name__} to run every {interval} seconds")
        # Immediately run the callback for testing
        callback({})

# Create a mock hassapi module
sys.modules['hassapi'] = type('hassapi', (), {'Hass': Hass})

# Now we can import the hydroinfo module
from hydroinfo import HydrologyData

# Create an instance of the HydrologyData class
hydrology_data = HydrologyData()

# Configure the app with the allomas_voa from the YAML file
hydrology_data.args = {"allomas_voa": "1649619E-97AB-11D4-BB62-00508BA24287"}

# Initialize the app
hydrology_data.initialize()

# Print the final states
print("\nFinal states:")
for entity_id, data in hydrology_data.states.items():
    print(f"{entity_id}: {data['state']} {data['attributes'].get('unit_of_measurement', '')}")
