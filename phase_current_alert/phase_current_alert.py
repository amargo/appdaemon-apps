import hassapi as hass
import datetime
import traceback

class PhaseCurrentAlert(hass.Hass):
    """
    AppDaemon app to monitor phase current sensors and send notifications when thresholds are exceeded.
    
    This app monitors the current values of three phases (L1, L2, L3) and sends notifications
    when any of them exceeds the configured threshold.
    """
    
    def initialize(self):
        """Initialize the app."""
        try:
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
            
            # Event name for threshold exceeded events
            self.event_name = self.args.get("event_name", "phase_current_alert.threshold_exceeded")
            
            # Time tracking for notification throttling
            self.last_notification_time = {
                "l1": None,
                "l2": None,
                "l3": None
            }
            
            # Store handles to listeners and timers
            self.listener_handles = []
            self.timer_handles = []
            
            # Set up listeners for current sensors
            self.listener_handles.append(self.listen_state(self.current_changed, self.sensor_l1))
            self.listener_handles.append(self.listen_state(self.current_changed, self.sensor_l2))
            self.listener_handles.append(self.listen_state(self.current_changed, self.sensor_l3))
            
            # Schedule a regular check
            self.timer_handles.append(self.run_every(self.check_current_values, "now", self.notification_interval))
            
            self.log(f"Phase Current Alert initialized with event: {self.event_name}")
            
            # Perform an initial check of all sensors
            self.run_in(self.check_current_values, 5)  # Check after 5 seconds to ensure sensors are loaded
            
            self.log(f"Phase Current Alert initialized with thresholds - L1: {self.threshold_l1}A, L2: {self.threshold_l2}A, L3: {self.threshold_l3}A, notification interval: {self.notification_interval} seconds")
        except Exception as e:
            self.log(f"Error during initialization: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def terminate(self):
        """Clean up when app is terminated."""
        try:
            # Cancel all registered listeners
            for handle in self.listener_handles:
                self.cancel_listen_state(handle)
            
            # Cancel all timers
            for handle in self.timer_handles:
                self.cancel_timer(handle)
                
            self.log("Phase Current Alert terminated cleanly")
        except Exception as e:
            self.log(f"Error during termination: {e}", level="ERROR")
    
    def current_changed(self, entity, attribute, old, new, kwargs):
        """Handle state changes for current sensors."""
        try:
            if new is not None and new != old:  
                self.check_specific_sensor(entity)
        except Exception as e:
            self.log(f"Error in current_changed: {e}", level="ERROR")
    
    def check_specific_sensor(self, entity):
        """Check a specific sensor against its threshold."""
        try:
            # Get the current state, handling potential None or unavailable values
            state = self.get_state(entity)
            if state is None or state in ["unavailable", "unknown"]:
                self.log(f"Sensor {entity} is {state}, skipping check", level="WARNING")
                return
                
            current_value = float(state)
            
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
                
                # Check if we should send a notification (throttle based on notification interval)
                now = datetime.datetime.now()
                last_time = self.last_notification_time[notification_key]
                
                if last_time is None or (now - last_time).total_seconds() >= self.notification_interval:
                    self.send_notification(phase, current_value, threshold)
                    self.last_notification_time[notification_key] = now
            
        except (ValueError, TypeError) as e:
            self.log(f"Error processing current value for {entity}: {e}", level="ERROR")
        except Exception as e:
            self.log(f"Unexpected error checking sensor {entity}: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def check_current_values(self, kwargs):
        """Check all current sensors against their thresholds."""
        try:
            self.log("Running scheduled check of all current sensors", level="DEBUG")
            self.check_specific_sensor(self.sensor_l1)
            self.check_specific_sensor(self.sensor_l2)
            self.check_specific_sensor(self.sensor_l3)
        except Exception as e:
            self.log(f"Error in scheduled check: {e}", level="ERROR")
            # Re-register the timer if it failed to ensure continuous monitoring
            self.timer_handles.append(self.run_every(self.check_current_values, "now", self.notification_interval))
    
    def send_notification(self, phase, current_value, threshold):
        """Send a notification about the high current and fire an event."""
        message = f"⚠️ High Current Alert: {phase} is at {current_value:.1f}A (threshold: {threshold}A). Please reduce load to avoid tripping the breaker."
        
        # Fire an event that other apps can listen for
        event_data = {
            "phase": phase,
            "current_value": current_value,
            "threshold": threshold,
            "timestamp": str(datetime.datetime.now())
        }
        self.log(f"Firing event: {self.event_name} with data: {event_data}")
        self.fire_event(self.event_name, **event_data)
        
        try:
            # Split the notification service into domain and service
            parts = self.notification_service.split('/')
            if len(parts) == 2:
                domain, service = parts
                self.call_service(f"{domain}/{service}", message=message)
                self.log(f"Notification sent: {message}")
            else:
                self.log(f"Invalid notification service format: {self.notification_service}", level="ERROR")
        except Exception as e:
            self.log(f"Failed to send notification: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
