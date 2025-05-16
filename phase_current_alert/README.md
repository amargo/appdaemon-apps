# Phase Current Alert

An AppDaemon app for Home Assistant that monitors current (amperage) sensors and sends notifications when thresholds are exceeded.

## Description

This app monitors the current values of three phases (L1, L2, L3) and sends notifications when any of them exceeds the configured threshold. This is particularly useful for EV charging scenarios where you want to avoid tripping circuit breakers when other appliances are running simultaneously.

## Features

- Monitors three separate current sensors (one for each phase)
- Configurable thresholds for each phase
- Sends notifications when current exceeds thresholds
- Throttles notifications to once per minute to avoid notification spam

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
