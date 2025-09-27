import appdaemon.plugins.hass.hassapi as hass
import datetime
import traceback

class EVChargeControl(hass.Hass):
    """
    AppDaemon app that controls EV charging based on phase current events.
    
    This app listens for events from the phase_current_alert app and controls
    EV charging to prevent overloading the electrical system.
    """
    
    def initialize(self):
        """Initialize the app."""
        try:
            self.log("EV Charge Control app initializing")
            
            # Get configuration parameters
            self.charging_sensor = self.args.get("charging_sensor")
            self.min_available_current = float(self.args.get("min_available_current", 6))
            self.overload_threshold = float(self.args.get("overload_threshold", 4))
            self.device_id = self.args.get("device_id")
            self.stop_charge_service = self.args.get("stop_charge_service")
            self.start_charge_service = self.args.get("start_charge_service")
            
            # Get event name to listen for
            self.event_name = self.args.get("event_name", "phase_current_alert.threshold_exceeded")
            
            # Get phase thresholds from phase_current_alert app or from config
            self.threshold_l1 = float(self.args.get("threshold_l1", 16))
            self.threshold_l2 = float(self.args.get("threshold_l2", 16))
            self.threshold_l3 = float(self.args.get("threshold_l3", 32))
            
            # Get sensor entities
            self.sensor_l1 = self.args.get("sensor_l1")
            self.sensor_l2 = self.args.get("sensor_l2")
            self.sensor_l3 = self.args.get("sensor_l3")
            
            # Notification service
            self.notification_service = self.args.get("notification_service", "notify/mobile_app")
            
            # Time tracking for notification throttling
            self.last_notification_time = None
            
            # Flag to track if charging was stopped by this app
            self.charging_stopped_by_app = False
            
            # Set up listener for the event
            self.listen_event(self.threshold_exceeded_event, self.event_name)
            self.log(f"Listening for events: {self.event_name}")
            
            # Set up listener for charging sensor
            self.listen_state(self.charging_state_changed, self.charging_sensor)
            self.log(f"Monitoring charging sensor: {self.charging_sensor}")
            
            # Schedule a regular check for resuming charging
            self.run_every(self.check_if_can_resume_charging, "now", 60)
            
            self.log("EV Charge Control initialized")
            
        except Exception as e:
            self.log(f"Error in initialize: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def threshold_exceeded_event(self, event_name, data, kwargs):
        """Handle threshold exceeded events from phase_current_alert."""
        try:
            self.log(f"Received event: {event_name} with data: {data}")
            
            # Extract event data
            phase = data.get("phase")
            current_value = data.get("current_value")
            threshold = data.get("threshold")
            
            if phase is None or current_value is None or threshold is None:
                self.log("Invalid event data received", level="WARNING")
                return
                
            # Check if charging control is needed
            if self.get_state(self.charging_sensor) == "on":
                # Calculate how much the current exceeds the threshold
                excess_current = current_value - threshold
                
                # If excess current is greater than the overload threshold, stop charging
                if excess_current > self.overload_threshold and not self.charging_stopped_by_app:
                    self.log(f"Current exceeds threshold by {excess_current:.1f}A which is more than the overload threshold of {self.overload_threshold}A")
                    self.stop_charging(phase, current_value, threshold)
                else:
                    self.log(f"Current exceeds threshold by {excess_current:.1f}A which is within the overload threshold of {self.overload_threshold}A")
                    
        except Exception as e:
            self.log(f"Error in threshold_exceeded_event: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def charging_state_changed(self, entity, attribute, old, new, kwargs):
        """Handle state changes for the charging sensor."""
        try:
            if new != old:
                self.log(f"Charging state changed from {old} to {new}")
                
                # If charging stopped and we didn't stop it, reset our flag
                if new == "off" and self.charging_stopped_by_app:
                    self.log("Charging stopped externally, resetting charging_stopped_by_app flag")
                    self.charging_stopped_by_app = False
                    
        except Exception as e:
            self.log(f"Error in charging_state_changed: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def stop_charging(self, phase, current_value, threshold):
        """Stop the EV charging."""
        try:
            log_message = f"Stopping charging due to high current on {phase}: {current_value}A (threshold: {threshold}A + {self.overload_threshold}A)"
            notification_message = f"🔌 Charging stopped: {phase} current reached {current_value:.1f}A (threshold: {threshold}A + {self.overload_threshold}A). Charging will resume when load decreases."
            
            # Control charging with common method
            self.control_charging(
                action="stop",
                service=self.stop_charge_service,
                log_message=log_message,
                notification_message=notification_message,
                set_charging_stopped_value=True
            )
                
        except Exception as e:
            self.log(f"Error stopping charging: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def check_if_can_resume_charging(self, kwargs=None):
        """Check if charging can be resumed based on available current."""
        try:
            # Only check if we previously stopped charging and charging is still off
            if not self.charging_stopped_by_app or self.get_state(self.charging_sensor) == "on":
                return
                
            # Check if there's enough available current
            has_enough_current, available_current = self.check_available_current()
            
            if has_enough_current:
                self.resume_charging(available_current)
                
        except Exception as e:
            self.log(f"Error checking if charging can be resumed: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
    
    def check_available_current(self):
        """Check if there is enough available current to resume charging.
        
        Returns:
            tuple: (has_enough_current, available_current)
        """
        try:
            # Get the current state of each phase
            l1_state = self.get_state(self.sensor_l1)
            l2_state = self.get_state(self.sensor_l2)
            l3_state = self.get_state(self.sensor_l3)
            
            # Skip check if any sensor is unavailable
            if any(state in [None, "unavailable", "unknown"] for state in [l1_state, l2_state, l3_state]):
                return False, 0
                
            # Calculate available current for each phase
            l1_current = float(l1_state)
            l2_current = float(l2_state)
            l3_current = float(l3_state)
            
            l1_available = self.threshold_l1 - l1_current
            l2_available = self.threshold_l2 - l2_current
            l3_available = self.threshold_l3 - l3_current
            
            # The minimum available current across all phases
            min_available = min(l1_available, l2_available, l3_available)
            
            return min_available >= self.min_available_current, min_available
            
        except Exception as e:
            self.log(f"Error checking available current: {e}", level="ERROR")
            return False, 0
    
    def resume_charging(self, available_current):
        """Resume the EV charging."""
        try:
            log_message = f"Resuming charging, available current: {available_current}A (minimum required: {self.min_available_current}A)"
            notification_message = f"⚡ Charging resumed: Available current is now {available_current:.1f}A (minimum required: {self.min_available_current}A)."
            
            # Control charging with common method
            self.control_charging(
                action="resume",
                service=self.start_charge_service,
                log_message=log_message,
                notification_message=notification_message,
                set_charging_stopped_value=False
            )
                
        except Exception as e:
            self.log(f"Error resuming charging: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
            
    def control_charging(self, action, service, log_message, notification_message, set_charging_stopped_value):
        """Common method to control charging (stop or resume).
        
        Args:
            action: The action being performed ("stop" or "resume")
            service: The service to call (stop_charge_service or start_charge_service)
            log_message: Message to log
            notification_message: Message to send as notification
            set_flag: Value to set for charging_stopped_by_app flag
        """
        try:
            # Log the action
            self.log(log_message)
            
            # Call the service to control charging
            parts = service.split('/')
            if len(parts) == 2:
                domain, service_name = parts
                self.call_service(f"{domain}/{service_name}", device_id=self.device_id)
            else:
                self.log(f"Invalid service format for {action} charging: {service}", level="ERROR")
                return
            
            self.charging_stopped_by_app = set_charging_stopped_value
            
            # Send notification
            self.send_notification(notification_message)
            
        except Exception as e:
            self.log(f"Error in control_charging ({action}): {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
            
    def send_notification(self, message):
        """Send a notification with throttling.
        
        Args:
            message: The message to send
        """
        try:
            # Only send notification if we haven't sent one recently
            now = datetime.datetime.now()
            if self.last_notification_time is None or (now - self.last_notification_time).total_seconds() >= 60:
                parts = self.notification_service.split('/')
                if len(parts) == 2:
                    domain, service = parts
                    escaped_msg = self.escape_markdown_v2(message)
                    self.call_service(f"{domain}/{service}", message=escaped_msg)
                    self.log(f"Notification sent: {escaped_msg}")
                    self.last_notification_time = now
                else:
                    self.log(f"Invalid notification service format: {self.notification_service}", level="ERROR")
            else:
                self.log(f"Notification throttled: {message}")
                
        except Exception as e:
            self.log(f"Error sending notification: {e}", level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")

    def escape_markdown_v2(self, text):
        """
        Escapes special characters for Telegram MarkdownV2.
        """
        text = text.replace('\\', '\\\\')
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return ''.join(['\\' + c if c in escape_chars else c for c in text])