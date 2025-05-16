import hassapi as hass
import datetime

class PhaseCurrentAlert(hass.Hass):
    """
    AppDaemon app to monitor phase current sensors and send notifications when thresholds are exceeded.
    
    This app monitors the current values of three phases (L1, L2, L3) and sends notifications
    when any of them exceeds the configured threshold.
    """
    
    def initialize(self):
        """Initialize the app."""
        self.log("Phase Current Alert app initializing")
        
        # Get configuration parameters
        self.threshold_l1 = float(self.args.get("threshold_l1", 16))
        self.threshold_l2 = float(self.args.get("threshold_l2", 16))
        self.threshold_l3 = float(self.args.get("threshold_l3", 32))
        
        self.sensor_l1 = self.args.get("sensor_l1", "sensor.pillanatnyi_aramerosseg_l1")
        self.sensor_l2 = self.args.get("sensor_l2", "sensor.pillanatnyi_aramerosseg_l2")
        self.sensor_l3 = self.args.get("sensor_l3", "sensor.pillanatnyi_aramerosseg_l3")
        
        self.notification_service = self.args.get("notification_service", "notify/mobile_app")
        
        # Get notification interval in seconds (default: 60 seconds = 1 minute)
        self.notification_interval = int(self.args.get("notification_interval", 60))
        
        # Time tracking for notification throttling
        self.last_notification_time = {
            "l1": None,
            "l2": None,
            "l3": None
        }
        
        # Set up listeners for the current sensors
        self.listen_state(self.current_changed, self.sensor_l1)
        self.listen_state(self.current_changed, self.sensor_l2)
        self.listen_state(self.current_changed, self.sensor_l3)
        
        # Schedule a regular check
        self.run_every(self.check_current_values, "now", self.notification_interval)
        
        self.log(f"Phase Current Alert initialized with thresholds - L1: {self.threshold_l1}A, L2: {self.threshold_l2}A, L3: {self.threshold_l3}A, notification interval: {self.notification_interval} seconds")
    
    def current_changed(self, entity, attribute, old, new, kwargs):
        """Handle state changes for current sensors."""
        self.check_specific_sensor(entity)
    
    def check_specific_sensor(self, entity):
        """Check a specific sensor against its threshold."""
        try:
            current_value = float(self.get_state(entity))
            
            # Determine which phase this is and get the corresponding threshold
            if entity == self.sensor_l1:
                phase = "L1"
                threshold = self.threshold_l1
                notification_key = "l1"
            elif entity == self.sensor_l2:
                phase = "L2"
                threshold = self.threshold_l2
                notification_key = "l2"
            elif entity == self.sensor_l3:
                phase = "L3"
                threshold = self.threshold_l3
                notification_key = "l3"
            else:
                return
            
            # Check if current exceeds threshold
            if current_value >= threshold:
                self.log(f"Current on {phase} is {current_value}A, which exceeds the threshold of {threshold}A")
                
                # Check if we should send a notification (throttle to once per minute)
                now = datetime.datetime.now()
                last_time = self.last_notification_time[notification_key]
                
                if last_time is None or (now - last_time).total_seconds() >= self.notification_interval:
                    self.send_notification(phase, current_value, threshold)
                    self.last_notification_time[notification_key] = now
            
        except (ValueError, TypeError) as e:
            self.log(f"Error processing current value for {entity}: {e}", level="ERROR")
    
    def check_current_values(self, kwargs):
        """Check all current sensors against their thresholds."""
        self.check_specific_sensor(self.sensor_l1)
        self.check_specific_sensor(self.sensor_l2)
        self.check_specific_sensor(self.sensor_l3)
    
    def send_notification(self, phase, current_value, threshold):
        """Send a notification about the high current."""
        message = f"⚠️ High Current Alert: {phase} is at {current_value:.1f}A (threshold: {threshold}A). Please reduce load to avoid tripping the breaker."
        
        try:
            self.call_service(self.notification_service, message=message)
            self.log(f"Notification sent: {message}")
        except Exception as e:
            self.log(f"Failed to send notification: {e}", level="ERROR")
