# SensorUnavailable

An AppDaemon app for Home Assistant that monitors sensors for availability and unchanged values.

## Description

This app monitors multiple sensors and sends notifications when:
1. A sensor becomes unavailable and remains unavailable for a specified period
2. A sensor's value doesn't change for a specified period (which might indicate the sensor is stuck)

This is particularly useful for detecting sensors that have stopped reporting or have battery issues.

## Features

- Monitors any number of sensors (temperature, motion, contact, etc.)
- Configurable check intervals for each sensor
- Sends notifications when sensors are unavailable
- Sends notifications when sensor values don't change for too long
- Fully configurable through YAML

## Installation

1. Copy the `sensor_unavailable` directory to your AppDaemon apps directory
2. Configure the app in your AppDaemon `apps.yaml` file or use the provided `sensor_unavailable.yaml`
3. Restart AppDaemon

## Configuration

Example configuration:

```yaml
SensorUnavailable:
  class: SensorUnavailable
  module: sensor_unavailable
  notification_service: notify/soulphone
  sensors:
    sensor.bedroom_temperature:
      friendly_name: Bedroom
      check_interval: 21600  # 6 hours in seconds
      same_val_check_enabled: true
    
    binary_sensor.motion_sensor_kitchen:
      friendly_name: Kitchen Motion
      check_interval: 86400  # 24 hours in seconds
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `notification_service` | Notification service to use | notify/soulphone |
| `sensors` | Dictionary of sensors to monitor | (see example) |

### Sensor Configuration Options

For each sensor, you can specify:

| Option | Description | Default |
|--------|-------------|---------|
| `friendly_name` | Human-readable name for the sensor | Entity ID |
| `check_interval` | Time in seconds to wait before alerting about unchanged values | 21600 (6 hours) |
| `same_val_check_enabled` | Whether to monitor for unchanged values | true |

## How It Works

The app creates a monitor for each configured sensor. Each monitor:

1. Listens for state changes of the sensor
2. If the sensor becomes unavailable, waits for the unavailable check interval (default 30 minutes) before sending a notification
3. If the sensor's value doesn't change for the specified check interval, sends a notification

For sensors that normally change values frequently (like temperature sensors), a shorter check interval is appropriate. For sensors that might not change for long periods (like window contacts), a longer check interval should be used.

## Customization

You can easily add or remove sensors from the configuration file. The check intervals should be adjusted based on how frequently you expect the sensor's value to change under normal conditions.

### Examples

- For temperature sensors in living spaces: 6 hours (21600 seconds) is usually appropriate
- For motion sensors: 24 hours (86400 seconds) or more depending on the area
- For window/door contact sensors: 40 hours (144000 seconds) or more is recommended
- For voltage sensors or critical systems: 30 minutes (1800 seconds) might be appropriate
