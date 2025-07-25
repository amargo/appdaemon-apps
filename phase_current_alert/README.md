# Phase Current Alert

An AppDaemon app for Home Assistant that monitors current (amperage) sensors, sends notifications when thresholds are exceeded, and fires events that other apps can listen to.

## Description

This app monitors the current values of three phases (L1, L2, L3) and sends notifications when any of them exceeds the configured threshold. This is particularly useful for EV charging scenarios where you want to avoid tripping circuit breakers when other appliances are running simultaneously.

## Features

- Monitors three separate current sensors (one for each phase)
- Configurable thresholds for each phase
- Sends notifications when current exceeds thresholds
- Throttles notifications to once per minute to avoid notification spam
- Fires events when thresholds are exceeded, allowing other apps to respond

## Installation

1. Copy the `phase_current_alert` directory to your AppDaemon apps directory
2. Configure the app in your AppDaemon `apps.yaml` file or use the provided `phase_current_alert.yaml`
3. Restart AppDaemon

## Configuration

Example configuration:

```yaml
PhaseCurrentAlert:
  class: PhaseCurrentAlert
  module: phase_current_alert
  threshold_l1: 16
  threshold_l2: 16
  threshold_l3: 32
  sensor_l1: sensor.pillanatnyi_aramerosseg_l1
  sensor_l2: sensor.pillanatnyi_aramerosseg_l2
  sensor_l3: sensor.pillanatnyi_aramerosseg_l3
  notification_service: notify/soulphone
  notification_interval: 60
  event_name: phase_current_alert.threshold_exceeded
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `threshold_l1` | Current threshold for L1 phase in amperes | 16 |
| `threshold_l2` | Current threshold for L2 phase in amperes | 16 |
| `threshold_l3` | Current threshold for L3 phase in amperes | 32 |
| `sensor_l1` | Entity ID for L1 phase current sensor | sensor.pillanatnyi_aramerosseg_l1 |
| `sensor_l2` | Entity ID for L2 phase current sensor | sensor.pillanatnyi_aramerosseg_l2 |
| `sensor_l3` | Entity ID for L3 phase current sensor | sensor.pillanatnyi_aramerosseg_l3 |
| `notification_service` | Notification service to use | notify/mobile_app |
| `notification_interval` | Interval in seconds between notifications | 60 |
| `event_name` | Event name that will be fired when thresholds are exceeded | phase_current_alert.threshold_exceeded |

### Events

When a threshold is exceeded, the app fires an event with the following data:

```json
{
  "phase": "L1",          // Phase name (L1, L2, or L3)
  "current_value": 18.5,  // Current value in amperes
  "threshold": 16.0,     // Threshold value in amperes
  "timestamp": "2025-07-25 10:15:30.123456"  // Timestamp of the event
}
```

Other apps can listen for this event and take appropriate actions, such as controlling EV charging or other high-power devices.
