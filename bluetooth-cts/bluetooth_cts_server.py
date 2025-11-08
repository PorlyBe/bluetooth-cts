#!/usr/bin/env python3
"""
Bluetooth Current Time Service (CTS) GATT Server for Home Assistant Add-on.

This server advertises the Current Time Service (0x1805) via Bluetooth GATT,
allowing devices like Glance Clock to automatically sync their time.
"""

import argparse
import logging
import sys
from datetime import datetime
from time import sleep
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import os
import requests
import pytz

# Constants
CTS_SERVICE_UUID = "00001805-0000-1000-8000-00805f9b34fb"
CURRENT_TIME_CHAR_UUID = "00002a2b-0000-1000-8000-00805f9b34fb"
LOCAL_TIME_INFO_CHAR_UUID = "00002a0f-0000-1000-8000-00805f9b34fb"

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"

logger = logging.getLogger(__name__)


class Application(dbus.service.Object):
    """DBus Application for GATT services."""
    
    def __init__(self, bus):
        self.path = "/"
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
    
    def get_path(self):
        return dbus.ObjectPath(self.path)
    
    def add_service(self, service):
        self.services.append(service)
    
    @dbus.service.method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for chrc in service.characteristics:
                response[chrc.get_path()] = chrc.get_properties()
        return response


class Service(dbus.service.Object):
    """DBus GATT Service."""
    
    PATH_BASE = "/org/bluez/gatt/service"
    
    def __init__(self, bus, index, uuid, primary):
        self.path = f"{self.PATH_BASE}{index}"
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)
    
    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                "UUID": self.uuid,
                "Primary": self.primary,
                "Characteristics": dbus.Array(
                    [chrc.get_path() for chrc in self.characteristics],
                    signature="o"
                ),
            }
        }
    
    def get_path(self):
        return dbus.ObjectPath(self.path)
    
    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)
    
    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise dbus.exceptions.DBusException(
                "org.bluez.Error.InvalidArguments",
                "Unknown interface"
            )
        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):
    """DBus GATT Characteristic."""
    
    def __init__(self, bus, index, uuid, flags, service):
        self.path = f"{service.path}/char{index:04d}"
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        dbus.service.Object.__init__(self, bus, self.path)
    
    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                "Service": self.service.get_path(),
                "UUID": self.uuid,
                "Flags": self.flags,
            }
        }
    
    def get_path(self):
        return dbus.ObjectPath(self.path)
    
    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise dbus.exceptions.DBusException(
                "org.bluez.Error.InvalidArguments",
                "Unknown interface"
            )
        return self.get_properties()[GATT_CHRC_IFACE]
    
    @dbus.service.method(GATT_CHRC_IFACE, out_signature="ay")
    def ReadValue(self, options):
        logger.debug(f"ReadValue called on {self.uuid}")
        return self.read_value(options)
    
    def read_value(self, options):
        """Override this method in subclass."""
        raise dbus.exceptions.DBusException(
            "org.bluez.Error.NotSupported",
            "Read not supported"
        )


class CurrentTimeCharacteristic(Characteristic):
    """Current Time Characteristic - provides current date and time."""
    
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, CURRENT_TIME_CHAR_UUID, ["read"], service
        )
    
    def read_value(self, options):
        """
        Return current time in CTS format.
        
        Format (10 bytes):
        - Year (2 bytes, little endian)
        - Month (1 byte, 1-12)
        - Day (1 byte, 1-31)
        - Hours (1 byte, 0-23)
        - Minutes (1 byte, 0-59)
        - Seconds (1 byte, 0-59)
        - Day of week (1 byte, 1=Monday, 7=Sunday)
        - Fractions256 (1 byte, 1/256th of a second)
        - Adjust reason (1 byte)
        """

    # Get local time with timezone awareness

        # Use TZ environment variable for timezone, fallback to system local time
        timezone = os.environ.get("TZ")
        if timezone:
            try:
                tz = pytz.timezone(timezone)
                now = datetime.now(tz)
                logger.info(f"[CTS] Using timezone: {timezone} | Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
            except Exception as e:
                logger.warning(f"[CTS] Invalid timezone '{timezone}', using system local time. Error: {e}")
                now = datetime.now().astimezone()
        else:
            now = datetime.now().astimezone()
            logger.info(f"[CTS] Using system local time: {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")

        # Convert to CTS format
        year_low = now.year & 0xFF
        year_high = (now.year >> 8) & 0xFF
        month = now.month
        day = now.day
        hours = now.hour
        minutes = now.minute
        seconds = now.second
        day_of_week = now.isoweekday()  # 1=Monday, 7=Sunday
        fractions = int((now.microsecond / 1000000.0) * 256)
        adjust_reason = 0  # No adjustment

        value = [
            dbus.Byte(year_low),
            dbus.Byte(year_high),
            dbus.Byte(month),
            dbus.Byte(day),
            dbus.Byte(hours),
            dbus.Byte(minutes),
            dbus.Byte(seconds),
            dbus.Byte(day_of_week),
            dbus.Byte(fractions),
            dbus.Byte(adjust_reason),
        ]

        logger.info(
            f"[CTS] BLE time sent: {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')} (Day {day_of_week})"
        )

        return value


class LocalTimeInfoCharacteristic(Characteristic):
    """Local Time Information Characteristic - provides timezone info."""
    
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index, LOCAL_TIME_INFO_CHAR_UUID, ["read"], service
        )
    
    def read_value(self, options):
        """
        Return local time information.
        
        Format (2 bytes):
        - Time zone (1 byte, offset in 15-minute increments from UTC, -48 to +56)
        - DST offset (1 byte, 0=standard time, 2=half hour, 4=daylight, 8=double daylight)
        """
        now = datetime.now().astimezone()
        offset = now.utcoffset()
        if offset is not None:
            utc_offset = offset.total_seconds()
        else:
            utc_offset = 0
        timezone_offset = int(utc_offset / 900)  # Convert to 15-minute increments
        dst_offset = 0  # Standard time (you could detect DST here if needed)

        value = [
            dbus.Byte(timezone_offset & 0xFF),
            dbus.Byte(dst_offset),
        ]

        logger.info(f"[CTS] BLE timezone offset sent: UTC{utc_offset/3600:+.1f}h (offset {timezone_offset}, DST {dst_offset})")
        return value


class CTSService(Service):
    """Current Time Service."""
    
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, CTS_SERVICE_UUID, True)
        
        # Add Current Time characteristic
        self.add_characteristic(CurrentTimeCharacteristic(bus, 0, self))
        
        # Add Local Time Information characteristic
        self.add_characteristic(LocalTimeInfoCharacteristic(bus, 1, self))


class Advertisement(dbus.service.Object):
    """BLE Advertisement."""
    
    PATH_BASE = "/org/bluez/gatt/advertisement"
    
    def __init__(self, bus, index, advertising_type):
        self.path = f"{self.PATH_BASE}{index}"
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.local_name = None
        self.include_tx_power = False
        dbus.service.Object.__init__(self, bus, self.path)
    
    def get_properties(self):
        properties = dict()
        properties["Type"] = self.ad_type
        if self.service_uuids is not None:
            properties["ServiceUUIDs"] = dbus.Array(self.service_uuids, signature="s")
        if self.local_name is not None:
            properties["LocalName"] = dbus.String(self.local_name)
        if self.include_tx_power:
            properties["IncludeTxPower"] = dbus.Boolean(self.include_tx_power)
        return {LE_ADVERTISEMENT_IFACE: properties}
    
    def get_path(self):
        return dbus.ObjectPath(self.path)
    
    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)
    
    def add_local_name(self, name):
        self.local_name = name
    
    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise dbus.exceptions.DBusException(
                "org.bluez.Error.InvalidArguments",
                "Unknown interface"
            )
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]
    
    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        logger.info("Advertisement released")


def register_advertisement(advertisement, adapter_path, bus):
    """Register the BLE advertisement."""
    adapter = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter_path),
        LE_ADVERTISING_MANAGER_IFACE
    )
    
    adapter.RegisterAdvertisement(
        advertisement.get_path(), {},
        reply_handler=lambda: logger.info("Advertisement registered"),
        error_handler=lambda error: logger.error(f"Failed to register advertisement: {error}")
    )


def find_adapter(bus):
    """Find the first available Bluetooth adapter."""
    remote_om = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, "/"),
        DBUS_OM_IFACE
    )
    objects = remote_om.GetManagedObjects()
    
    for path, ifaces in objects.items():
        adapter = ifaces.get("org.bluez.Adapter1")
        if adapter is not None:
            return path
    
    return None


def register_application(app, adapter_path, bus):
    """Register the GATT application."""
    adapter = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter_path),
        GATT_MANAGER_IFACE
    )
    
    adapter.RegisterApplication(
        app.get_path(), {},
        reply_handler=lambda: logger.info("GATT application registered"),
        error_handler=lambda error: logger.error(f"Failed to register application: {error}")
    )


def main():
    # Log the detected local time and timezone at startup
    timezone = os.environ.get("TZ")
    if timezone:
        try:
            tz = pytz.timezone(timezone)
            local_now = datetime.now(tz)
            logger.info(f"[CTS] Startup time: {local_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')} (timezone: {timezone})")
        except Exception as e:
            local_now = datetime.now().astimezone()
            logger.warning(f"[CTS] Invalid timezone '{timezone}' at startup, using system local time. Error: {e}")
            logger.info(f"[CTS] Startup time: {local_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    else:
        local_now = datetime.now().astimezone()
        logger.info(f"[CTS] Startup time: {local_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
    parser = argparse.ArgumentParser(description="Bluetooth CTS Time Sync Server")
    parser.add_argument("--device-name", default="HomeAssistant-CTS", help="Bluetooth device name")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    logger.info("=" * 60)
    logger.info("Bluetooth CTS Time Sync Server")
    logger.info("=" * 60)
    logger.info(f"Device name: {args.device_name}")
    logger.info(f"Log level: {args.log_level}")

    # Log the detected local time and timezone at startup
    local_now = datetime.now().astimezone()
    logger.info(f"Startup local time: {local_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')} | tzinfo: {local_now.tzinfo}")
    
    # Initialize DBus
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    
    # Find Bluetooth adapter
    adapter_path = find_adapter(bus)
    if not adapter_path:
        logger.error("No Bluetooth adapter found!")
        return 1
    
    logger.info(f"Using Bluetooth adapter: {adapter_path}")
    
    # Create and register GATT application
    app = Application(bus)
    cts_service = CTSService(bus, 0)
    app.add_service(cts_service)
    
    logger.info("Registering Current Time Service...")
    register_application(app, adapter_path, bus)
    
    # Create and register advertisement
    adv = Advertisement(bus, 0, "peripheral")
    adv.add_service_uuid(CTS_SERVICE_UUID)
    adv.add_local_name(args.device_name)
    adv.include_tx_power = True
    
    logger.info("Registering advertisement...")
    register_advertisement(adv, adapter_path, bus)
    
    # Start main loop
    logger.info("CTS server is running - devices can now sync time")
    logger.info("Press Ctrl+C to stop")
    
    mainloop = GLib.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
