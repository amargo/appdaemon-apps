# EV Charge Control

An AppDaemon app for Home Assistant that controls EV charging based on phase current events from the Phase Current Alert app.

## Description

This app listens for threshold exceeded events from the Phase Current Alert app and automatically controls EV charging to prevent overloading your electrical system. It will stop charging when any phase current exceeds the threshold plus an overload margin, and resume charging when sufficient current is available again.

## Features

- Listens for events from the Phase Current Alert app
- Automatically stops EV charging when current exceeds threshold plus overload margin
- Automatically resumes charging when sufficient current is available
- Sends detailed notifications about charging status changes
- Configurable parameters for fine-tuning behavior

## Installation

1. Copy the `ev_charge_control` directory to your AppDaemon apps directory
2. Configure the app in your `apps.yaml` file or create a separate `ev_charge_control.yaml` file
3. Restart AppDaemon

## Configuration

Example configuration:

```yaml
ev_charge_control:
  module: ev_charge_control
  class: EVChargeControl
  
  # Event to listen for
  event_name: phase_current_alert.threshold_exceeded
  
  # Charging sensor and control parameters
  charging_sensor: binary_sensor.e_niro_ev_battery_charge
  min_available_current: 6
  overload_threshold: 4
  device_id: c3c81ec5-1fe4-4459-b6ba-474ea5acce79
  stop_charge_service: kia_uvo/stop_charge
  start_charge_service: kia_uvo/start_charge
  
  # Current sensors and thresholds (should match phase_current_alert settings)
  sensor_l1: sensor.pillanatnyi_aramerosseg_l1
  sensor_l2: sensor.pillanatnyi_aramerosseg_l2
  sensor_l3: sensor.pillanatnyi_aramerosseg_l3
  threshold_l1: 16
  threshold_l2: 16
  threshold_l3: 32
  
  # Notification service
  notification_service: notify/soulphone
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `event_name` | Event to listen for from Phase Current Alert app | phase_current_alert.threshold_exceeded |
| `charging_sensor` | Binary sensor that indicates if charging is active | binary_sensor.e_niro_ev_battery_charge |
| `min_available_current` | Minimum available current required to resume charging (A) | 6 |
| `overload_threshold` | Extra current allowed over threshold before stopping charging (A) | 4 |
| `device_id` | Device ID for the EV charger | c3c81ec5-xxxx-xxxx-xxxx-xxxxxxxxxxxx |
| `stop_charge_service` | Service to call to stop charging | kia_uvo/stop_charge |
| `start_charge_service` | Service to call to resume charging | kia_uvo/start_charge |
| `sensor_l1` | Entity ID for L1 phase current sensor | sensor.pillanatnyi_aramerosseg_l1 |
| `sensor_l2` | Entity ID for L2 phase current sensor | sensor.pillanatnyi_aramerosseg_l2 |
| `sensor_l3` | Entity ID for L3 phase current sensor | sensor.pillanatnyi_aramerosseg_l3 |
| `threshold_l1` | Current threshold for L1 phase in amperes | 16 |
| `threshold_l2` | Current threshold for L2 phase in amperes | 16 |
| `threshold_l3` | Current threshold for L3 phase in amperes | 32 |
| `notification_service` | Notification service to use | notify/mobile_app |

## Usage

The app works automatically once configured. It will:

1. Listen for threshold exceeded events from the Phase Current Alert app
2. When an event is received, check if the current exceeds the threshold plus overload margin
3. If overloaded and charging is active, stop charging and send a notification
4. Periodically check if enough current is available to resume charging
5. When sufficient current is available, resume charging and send a notification

No manual intervention is required once set up.
