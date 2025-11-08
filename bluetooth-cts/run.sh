#!/bin/bash

# Source bashio for Home Assistant add-ons
source /usr/lib/bashio/bashio.sh

# Read config directly from options.json with fallbacks
CONFIG_FILE="/data/options.json"

if [ -f "$CONFIG_FILE" ]; then
    DEVICE_NAME=$(jq -r '.device_name // "HomeAssistant-CTS"' "$CONFIG_FILE")
    LOG_LEVEL=$(jq -r '.log_level // "info"' "$CONFIG_FILE")
else
    DEVICE_NAME="HomeAssistant-CTS"
    LOG_LEVEL="info"
fi

bashio::log.info "Starting Bluetooth CTS Time Sync..."
bashio::log.info "Device name: ${DEVICE_NAME}"
bashio::log.info "Log level: ${LOG_LEVEL}"

if ! pgrep -x "dbus-daemon" > /dev/null; then
    bashio::log.info "Starting D-Bus..."
    mkdir -p /var/run/dbus
    dbus-daemon --system &
    sleep 2
fi

# Check if bluetoothd is already running (from host)
if pgrep -x "bluetoothd" > /dev/null; then
    bashio::log.info "Using host bluetoothd"
else
    if ! pgrep -x "bluetoothd" > /dev/null; then
        bashio::log.info "Starting Bluetooth daemon..."
        /usr/lib/bluetooth/bluetoothd --experimental &
        sleep 3
    fi
fi

# Wait for adapter to appear
bashio::log.info "Waiting for Bluetooth adapter..."
for i in {1..10}; do
    if bluetoothctl list | grep -q "Controller"; then
        bashio::log.info "Bluetooth adapter found"
        break
    fi
    sleep 1
done

bashio::log.info "Configuring Bluetooth adapter..."
(
  sleep 1
  echo "power on"
  sleep 1
  echo "system-alias ${DEVICE_NAME}"
  sleep 1
  echo "discoverable on"
  sleep 1
  echo "discoverable-timeout 0"
  sleep 1
  echo "pairable off"
  sleep 1
  echo "exit"
) | bluetoothctl

# Give bluetoothctl time to complete
sleep 2

# Export timezone from add-on config if set
TZ_VALUE=$(jq -r '.timezone // empty' /data/options.json)
if [ -n "$TZ_VALUE" ]; then
  export TZ="$TZ_VALUE"
  bashio::log.info "Using timezone from config: $TZ_VALUE"
fi

bashio::log.info "Starting Current Time Service..."
python3 /bluetooth_cts_server.py --device-name "${DEVICE_NAME}" --log-level "${LOG_LEVEL}"