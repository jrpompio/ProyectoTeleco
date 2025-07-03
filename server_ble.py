#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Servidor BLE GATT para IE0527 - Diseño Final
# Publica un servicio BLE con autenticación, SSID y PASS.
#
# Requisitos:
# - BlueZ >= 5.50 con soporte --experimental.
# - pydbus, python-dbus y gi.repository.
#
# Ejecutar con permisos de superusuario.

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisement1'

MAIN_LOOP = None

# UUIDs según el requerimiento
SERVICE_UUID = '12345678-1234-1234-1234-1234567890ab'
CHAR_AUTH_UUID = 'abcd1234-5678-90ab-cdef-1234567890ab'
CHAR_SSID_UUID = 'abcd1234-5678-90ab-cdef-1234567890ac'
CHAR_PASS_UUID = 'abcd1234-5678-90ab-cdef-1234567890ad'

# Datos fijos
AUTH_TOKEN = b'hacking'
SSID = b'Fala lalala'
PASSWORD = b'sopadefrijoles13'

AUTHORIZED = False

# Utils --------------------------------------------------------------

def register_app_cb():
    print('> GATT application registered')

def register_app_error_cb(error):
    print('> Failed to register application: ' + str(error))
    MAIN_LOOP.quit()

def register_ad_cb():
    print('> Advertisement registered')

def register_ad_error_cb(error):
    print('> Failed to register advertisement: ' + str(error))
    MAIN_LOOP.quit()

# GATT Application ---------------------------------------------------

class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 implementation
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(MyService(bus, 0))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for char in service.characteristics:
                response[char.get_path()] = char.get_properties()
        return response

# GATT Service -------------------------------------------------------

class MyService(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus, index):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = SERVICE_UUID
        self.primary = True
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

        self.add_characteristic(AuthCharacteristic(bus, 0, self))
        self.add_characteristic(SSIDCharacteristic(bus, 1, self))
        self.add_characteristic(PASSCharacteristic(bus, 2, self))

    def get_properties(self):
        return {
            'org.bluez.GattService1': {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    [char.get_path() for char in self.characteristics],
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

# GATT Characteristic Base -------------------------------------------

class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.service = service
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            'org.bluez.GattCharacteristic1': {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

# Característica: Autenticación --------------------------------------

class AuthCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, CHAR_AUTH_UUID,
                                ['write'], service)

    @dbus.service.method('org.bluez.GattCharacteristic1',
                         in_signature='aya{sv}')
    def WriteValue(self, value, options):
        global AUTHORIZED
        print(f'> Auth WriteValue: {value}')
        if bytes(value) == AUTH_TOKEN:
            AUTHORIZED = True
            print('> Autenticación correcta')
        else:
            AUTHORIZED = False
            print('> Autenticación incorrecta')

    @dbus.service.method('org.bluez.GattCharacteristic1',
                         in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        return dbus.Array(AUTH_TOKEN, signature='y')

# Característica: SSID -----------------------------------------------

class SSIDCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, CHAR_SSID_UUID,
                                ['read'], service)

    @dbus.service.method('org.bluez.GattCharacteristic1',
                         in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        if AUTHORIZED:
            print('> SSID leído autorizado')
            return dbus.Array(SSID, signature='y')
        else:
            print('> SSID leído NO autorizado')
            return dbus.Array(b'', signature='y')

# Característica: PASS -----------------------------------------------

class PASSCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, CHAR_PASS_UUID,
                                ['read'], service)

    @dbus.service.method('org.bluez.GattCharacteristic1',
                         in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        if AUTHORIZED:
            print('> PASS leído autorizado')
            return dbus.Array(PASSWORD, signature='y')
        else:
            print('> PASS leído NO autorizado')
            return dbus.Array(b'', signature='y')

# LE Advertisement ---------------------------------------------------

class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = [SERVICE_UUID]
        self.local_name = 'ServidorWiFi-BLE'
        self.include_tx_power = True
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            ADVERTISING_MANAGER_IFACE: {
                'Type': self.ad_type,
                'ServiceUUIDs': dbus.Array(self.service_uuids, signature='s'),
                'LocalName': dbus.String(self.local_name),
                'IncludeTxPower': dbus.Boolean(self.include_tx_power)
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        return self.get_properties()[ADVERTISING_MANAGER_IFACE]

    @dbus.service.method(ADVERTISING_MANAGER_IFACE)
    def Release(self):
        print('> Advertisement released')

# Main ---------------------------------------------------------------

def main():
    global MAIN_LOOP

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('> BLE adapter no encontrado')
        return

    service_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                     GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)

    app = Application(bus)
    adv = Advertisement(bus, 0, 'peripheral')

    MAIN_LOOP = GLib.MainLoop()

    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)

    ad_manager.RegisterAdvertisement(adv.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)

    MAIN_LOOP.run()

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for path, interfaces in objects.items():
        if LE_ADVERTISING_MANAGER_IFACE in interfaces and \
           GATT_MANAGER_IFACE in interfaces:
            return path
    return None

if __name__ == '__main__':
    main()

