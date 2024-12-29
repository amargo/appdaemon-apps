import hassapi as hass
import json
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from itertools import islice

BASE_URL_TEMPLATE = "https://www.vizugy.hu/?mapModule=OpGrafikon&AllomasVOA={allomas_voa}&mapData=Idosor"

class HydrologyData(hass.Hass):
    def initialize(self):
        # Retrieve the 'allomas_voa' parameter from configuration
        self.allomas_voa = self.args.get("allomas_voa")
        if not self.allomas_voa:
            self.log("Missing 'allomas_voa' in configuration", level="ERROR")
            return

        # Schedule the `read_data` function to run every hour
        interval_seconds = 1 * 60 * 60
        self.run_every(self.read_data, "now", interval_seconds)

    def read_data(self, kwargs):
        try:
            # Use fake_useragent to generate a dynamic User-Agent header
            user_agent = UserAgent().random
            headers = {"User-Agent": user_agent}

            # Construct the URL with the provided 'allomas_voa'
            base_url = BASE_URL_TEMPLATE.format(allomas_voa=self.allomas_voa)

            # Make an HTTP GET request
            response = requests.get(base_url, headers=headers, verify=True)

            # Check if the HTTP response status is 200 (OK)
            if response.status_code != 200:
                self.log(f"HTTP error: {response.status_code}", level="ERROR")
                return

            # Parse the HTML content
            html_content = BeautifulSoup(response.content, "html.parser")
            table = html_content.find("table", class_="vizmercelista")
            if not table:
                self.log("The 'vizmercelista' table was not found.", level="ERROR")
                return

            # Iterate through the rows, skipping the header row
            allomas_list = islice(table.find_all("tr"), 1, None)
            for row in allomas_list:
                # Extract columns from the row
                cols = row.find_all("td")
                cols = [ele.text.strip() for ele in cols]

                # Log the content of cols
                self.log(f"Extracted columns: {cols}")

                # Extract relevant values
                if len(cols) < 4:
                    self.log(f"Incomplete data in row: {cols}", level="WARNING")
                    continue

                timestamp = cols[0]
                water_level = cols[1]  # Vízállás (cm)
                water_temp = cols[3]  # Vízhő (°C)

                # Validate and process water level sensor
                if water_level and water_level.isdigit():
                    water_level_value = int(water_level)
                    self.set_state(
                        "sensor.agard_water_level",
                        state=water_level_value,
                        unit_of_measurement="cm",
                        attributes={
                            "state_class": "measurement",
                            "last_changed": timestamp,
                            "unit_of_measurement": "cm",
                            "friendly_name": "Agárd Water Level",
                            "device_class": "measurement",
                        },
                    )
                    self.log(f"Water level sensor updated: {timestamp} - {water_level_value} cm")
                else:
                    self.log(f"Invalid water level value: {water_level}", level="WARNING")

                # Validate and process water temperature sensor
                try:
                    if water_temp:
                        water_temp_value = float(water_temp)
                        self.set_state(
                            "sensor.agard_water_temperature",
                            state=water_temp_value,
                            unit_of_measurement="°C",
                            attributes={
                                "state_class": "measurement",
                                "last_changed": timestamp,
                                "unit_of_measurement": "°C",
                                "friendly_name": "Agárd Water Temperature",
                                "device_class": "temperature",
                            },
                        )
                        self.log(f"Water temperature sensor updated: {timestamp} - {water_temp_value} °C")
                except ValueError as e:
                    self.log(f"Failed to convert water temperature value: {water_temp} - Error: {e}", level="WARNING")

                break  # Only process the first valid row

        except Exception as e:
            # Log any unexpected errors
            self.log(f"An error occurred: {e}", level="ERROR")
