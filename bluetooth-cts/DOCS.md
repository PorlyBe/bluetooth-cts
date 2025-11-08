# Bluetooth CTS Time Sync Add-on Documentation

## Overview
This add-on provides a Bluetooth Current Time Service (CTS) GATT server for Home Assistant. It allows BLE clocks and devices to sync their time with Home Assistant, using the configured timezone.

## Configuration Options
- **device_name**: Name advertised over Bluetooth (default: HomeAssistant-CTS)
- **log_level**: Logging verbosity (debug, info, warning, error)
- **timezone**: IANA timezone name (e.g., Europe/Berlin)

## Timezone
- The timezone is set via the add-on UI and passed as the `TZ` environment variable.
- Use a valid IANA timezone name (e.g., Europe/Berlin, America/New_York).
- If not set, UTC is used by default.

## Verifying Operation
- Use a BLE scanner (e.g., nRF Connect) to verify the device advertises the CTS service (UUID 0x1805).
- BLE clients should be able to read the current time without pairing.

## Security
- The add-on only requests the minimum privileges required for BLE operation.
- No pairing or authentication is required for time sync.

## Advanced
- For advanced troubleshooting, check the logs in Home Assistant Supervisor.
- The add-on can be run manually for local testing.

## Support
For help and feature requests, visit: https://github.com/your-repo/bluetooth-cts
