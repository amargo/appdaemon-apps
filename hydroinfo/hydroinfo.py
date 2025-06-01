import hassapi as hass
import json
import requests
import time
import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from itertools import islice

BASE_URL_TEMPLATE = "https://www.vizugy.hu/?mapModule=OpGrafikon&AllomasVOA={allomas_voa}&mapData=Idosor"

class HydrologyData(hass.Hass):
    def initialize(self):
        self.log(f"HydrologyData initializing at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}", level="INFO")
        
        # Retrieve the 'allomas_voa' parameter from configuration
        self.allomas_voa = self.args.get("allomas_voa")
        if not self.allomas_voa:
            self.log("Missing 'allomas_voa' in configuration", level="ERROR")
            return
        
        self.log(f"Using allomas_voa: {self.allomas_voa}", level="INFO")

        # Schedule the `read_data` function to run every hour
        interval_seconds = 1 * 60 * 60
        self.log(f"Scheduling read_data to run every {interval_seconds} seconds", level="INFO")
        
        # Run immediately and then every hour
        self.log("Running read_data immediately", level="INFO")
        self.read_data({})
        
        # Schedule for future runs
        self.run_every(self.read_data, "now+10", interval_seconds)

    def _fetch_data(self):
        """Fetch data from the water monitoring website"""
        user_agent = UserAgent().random
        headers = {"User-Agent": user_agent}
        self.log(f"Generated User-Agent: {user_agent}", level="INFO")

        base_url = BASE_URL_TEMPLATE.format(allomas_voa=self.allomas_voa)
        self.log(f"Requesting data from URL: {base_url}", level="INFO")

        request_start = time.time()
        response = requests.get(base_url, headers=headers, verify=True)
        request_time = time.time() - request_start
        self.log(f"HTTP request completed in {request_time:.2f} seconds with status code: {response.status_code}", level="INFO")
        
        if response.status_code != 200:
            self.log(f"HTTP error: {response.status_code}", level="ERROR")
            return None
            
        return response

    def _parse_html(self, response):
        """Parse HTML content and extract the data table"""
        parse_start = time.time()
        self.log("Parsing HTML content", level="INFO")
        
        html_content = BeautifulSoup(response.content, "html.parser")
        table = html_content.find("table", class_="vizmercelista")
        
        parse_time = time.time() - parse_start
        self.log(f"HTML parsing completed in {parse_time:.2f} seconds", level="INFO")
        
        if not table:
            self.log("The 'vizmercelista' table was not found.", level="ERROR")
            return None
            
        return table

    def _process_water_level(self, timestamp, water_level):
        """Process and update water level sensor"""
        if not water_level or not water_level.isdigit():
            self.log(f"Invalid water level value: {water_level}", level="WARNING")
            return False
            
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
        return True

    def _process_water_temperature(self, timestamp, water_temp):
        """Process and update water temperature sensor"""
        if not water_temp:
            return False
            
        if water_temp == '-':
            self.log(f"Water temperature not available (value is '-')", level="INFO")
            return False
            
        if not water_temp.replace('.', '', 1).isdigit():
            self.log(f"Invalid water temperature value: {water_temp}", level="WARNING")
            return False
            
        try:
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
            return True
        except ValueError as e:
            self.log(f"Failed to convert water temperature value: {water_temp} - Error: {e}", level="WARNING")
            return False

    def _is_valid_row(self, cols):
        """Check if a row has enough valid data"""
        if len(cols) < 4:
            return False
            
        non_empty_count = sum(1 for col in cols if col.strip())
        return non_empty_count >= 2

    def read_data(self, kwargs):
        start_time = time.time()
        self.log(f"Starting read_data at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}", level="INFO")
        
        try:
            # Fetch data from the website
            response = self._fetch_data()
            if not response:
                return

            # Parse the HTML content
            table = self._parse_html(response)
            if not table:
                return

            # Process the data rows
            processed_water_level = False
            processed_water_temp = False
            
            # Iterate through the rows, skipping the header row
            allomas_list = islice(table.find_all("tr"), 1, None)
            
            for row in allomas_list:
                # Extract columns from the row
                cols = [ele.text.strip() for ele in row.find_all("td")]
                self.log(f"Extracted columns: {cols}")
                
                # Skip invalid rows
                if not self._is_valid_row(cols):
                    self.log(f"Not enough valid data, skipping row: {cols}", level="WARNING")
                    continue
                
                timestamp = cols[0]
                water_level = cols[1]  # Vízállás (cm)
                water_temp = cols[3]  # Vízhő (°C)
                
                # Process water level if not already processed
                if not processed_water_level:
                    processed_water_level = self._process_water_level(timestamp, water_level)
                
                # Process water temperature
                processed_water_temp = self._process_water_temperature(timestamp, water_temp)
                
                # Stop processing after the first valid row with temperature
                if processed_water_temp:
                    break
                    
        except Exception as e:
            # Log any unexpected errors
            self.log(f"An error occurred: {e}", level="ERROR")
        finally:
            execution_time = time.time() - start_time
            self.log(f"read_data execution completed in {execution_time:.2f} seconds at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}", level="INFO")
