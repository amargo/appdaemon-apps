import hassapi as hass

class SensorMonitor:
    def __init__(self, app, entity_name, friendly_name, check_interval, same_val_check_enabled=True):
        """
        Monitors a specific sensor entity for availability and value changes.

        Args:
            app: Reference to the parent AppDaemon app.
            entity_name (str): The full entity ID of the sensor.
            friendly_name (str): A human-readable name for the sensor.
            check_interval (int): Time in seconds to check for changes or availability.
            same_val_check_enabled (bool): Whether to monitor for unchanged values.
        """
        self.app = app
        self.entity_name = entity_name
        self.friendly_name = friendly_name
        self.check_interval = check_interval
        self.same_val_check_enabled = same_val_check_enabled
        self.unavailable = False
        self.unavailable_timer = None
        self.unavailable_check_interval=30*60
        self.previous_value = None
        self.same_val_timer = None

        # Listen for state changes of the entity
        self.app.listen_state(self.on_entity_changed, self.entity_name)

        # If enabled, set a timer to monitor for unchanged values
        if self.same_val_check_enabled:
            self.same_val_timer = self.app.run_in(self.on_sensor_stays_same, self.check_interval)

    def on_entity_changed(self, entity, attribute, old, new, kwargs):
        """Handles changes in the sensor's state."""
        if new and new.lower() in ["unknown", "unavailable"]:
            if not self.unavailable_timer:
                self.unavailable_timer = self.app.run_in(self.notify_unavailable, self.unavailable_check_interval)
        else:
            # Reset the "unavailable" state timer if the sensor becomes available
            if self.unavailable_timer:
                self.app.cancel_timer(self.unavailable_timer)
                self.unavailable_timer = None
        #     if not self.unavailable:
        #         self.unavailable = True
        #         self.app.call_service(
        #             "notify/soulphone",
        #             message=f"{self.friendly_name} sensor is unavailable."
        #         )
        # else:
        #     if self.unavailable:
        #         self.unavailable = False
        #         self.app.call_service(
        #             "notify/soulphone",
        #             message=f"{self.friendly_name} sensor is back online."
        #         )

            # Reset value change monitoring if enabled
            if self.same_val_check_enabled:
                if self.same_val_timer:
                    self.app.cancel_timer(self.same_val_timer)
                self.previous_value = new
                self.same_val_timer = self.app.run_in(self.on_sensor_stays_same, self.check_interval)


    def notify_unavailable(self, kwargs):
        """Sends a notification if the sensor remains unavailable."""
        self.app.log(f"Sensor {self.friendly_name} is still unavailable after {self.unavailable_check_interval} seconds.")
        message=f"{self.friendly_name} sensor is unavailable for {self.unavailable_check_interval // 60} minutes."
        escaped_msg = self.escape_markdown_v2(message)
        self.app.call_service(self.app.notification_service, escaped_msg)
        self.unavailable_timer = None  # Reset the timer


    def on_sensor_stays_same(self, kwargs):
        """Handles cases where the sensor value does not change over the interval."""
        current_value = self.app.get_state(self.entity_name)
        if current_value == self.previous_value:
            self.unavailable = True
            interval_minutes = convert_to_minutes(self.check_interval)
            message=f"{self.friendly_name} sensor value has not changed for {interval_minutes} minutes."
            escaped_msg = self.escape_markdown_v2(message)
            self.app.call_service(self.app.notification_service, escaped_msg)
        else:
            self.unavailable = False
            self.previous_value = current_value

        # Reschedule the same value check if still enabled
        if self.same_val_check_enabled:
            self.same_val_timer = self.app.run_in(self.on_sensor_stays_same, self.check_interval)

def convert_to_minutes(seconds):
    interval_minutes = seconds // 60  # Convert seconds to minutes
    return interval_minutes

class SensorUnavailable(hass.Hass):

    def initialize(self):
        """
        Initializes the app and sets up monitors for multiple sensors.
        """
        self.entities_to_watch = {}
        
        # Get notification service from config
        self.notification_service = self.args.get("notification_service", "notify/soulphone")

        # Add sensors to monitor from configuration
        sensors_config = self.args.get("sensors", {})
        
        # If sensors are configured in the YAML, use those
        if sensors_config:
            for entity_id, config in sensors_config.items():
                friendly_name = config.get("friendly_name", entity_id)
                check_interval = config.get("check_interval", 6 * 60 * 60)  # Default 6 hours
                same_val_check = config.get("same_val_check_enabled", True)
                
                self.create_sensor_monitor(
                    entity_id, 
                    friendly_name, 
                    check_interval=check_interval,
                    same_val_check_enabled=same_val_check
                )

        # Log the sensors being monitored
        self.log("Monitoring started for the following sensors:")
        for entity_name, monitor in self.entities_to_watch.items():
            interval_minutes = convert_to_minutes(monitor.check_interval)
            self.log(f"- {entity_name} ({monitor.friendly_name}): Check interval {interval_minutes} minutes")

    def escape_markdown_v2(self, text):
        """
        Escapes special characters for Telegram MarkdownV2.
        """
        text = text.replace('\\', '\\\\')
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return ''.join(['\\' + c if c in escape_chars else c for c in text])

    def create_sensor_monitor(self, entity_name, friendly_name, check_interval=6*60*60, same_val_check_enabled=True):
        """
        Creates a monitor for a given sensor entity.

        Args:
            entity_name (str): The entity ID with prefix.
            friendly_name (str): A human-readable name for the sensor.
            check_interval (int): Interval to check for unchanged values.
            same_val_check_enabled (bool): Whether to enable unchanged value monitoring.
            entity_prefix (str): The prefix to prepend to the entity ID.
        """
        full_entity_name = f"{entity_name}"
        monitor = SensorMonitor(self, full_entity_name, friendly_name, check_interval, same_val_check_enabled)
        self.entities_to_watch[full_entity_name] = monitor
