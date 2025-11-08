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

## License

MIT License

Copyright (c) 2025 [Your Name or Organization]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
