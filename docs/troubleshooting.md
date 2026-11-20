# Bluetooth troubleshooting

**English** | [Deutsch](troubleshooting.de.md) · [Back to the overview](../README.md)

## Basics

- **One connection at a time.** The Smart Connect module accepts only one Bluetooth connection. While Home Assistant is connected, the JURA app cannot connect, and the other way round.
- **No advertising while connected.** While a device is connected, the machine does not advertise and cannot be found by others.
- **Active scanning is required for setup.** The machine sends its model only in the scan response. A receiver that only listens passively is not enough.
- **Heartbeat.** The machine drops a connection after about 10 seconds without a heartbeat. The integration sends one every 9 seconds.

## Receiver

A good receiver close to the machine matters more than anything else.

- **ESPHome Bluetooth proxy (recommended):** an ESP32 with [`bluetooth_proxy`](https://esphome.io/components/bluetooth_proxy.html) and `active: true`, close to the machine. We use an M5Stack AtomS3U (ESP32-S3 as a USB stick) in a wall socket with USB next to the machine. Any ESP32 with Bluetooth should work.
  ```yaml
  esp32_ble_tracker:
    scan_parameters:
      active: true
  bluetooth_proxy:
    active: true
  ```
- **Bluetooth adapter on the Home Assistant host:** see the [Home Assistant list](https://www.home-assistant.io/integrations/bluetooth/). AlexxIT had no stable connection with five adapters (*Unbranded CSR clone detected*); only an adapter with a `CSR8510A10` chip worked reliably.

For comparison: a MacBook a few metres from our WE6 saw the machine at −72 to −84 dBm and could read everything, but lost the connection more often towards −84 dBm.

## The machine is not offered during setup

1. Is the machine on? It only advertises while it is on.
2. Close the JURA app completely (also swipe it away in the app switcher) or turn off Bluetooth on the phone.
3. Is a receiver with active scanning close enough?
4. If nothing helps: switch the machine fully off and on again. This resets the module.

## Values do not update, connection shows "off"

- The machine is off or in standby: normal. The entities keep their last values.
- Another device is connected, usually the JURA app.
- The receiver is too far away or the proxy is offline: check the device of the proxy in Home Assistant.
- Turn on debug logging (*Settings › Devices & services › JURA Coffee Machines › Enable debug logging*) and look for `heartbeat error` or `ping error`.

## Another device cannot connect

The connection switch of the integration disconnects only briefly: the next reading (within a minute) connects again. To keep the machine free, for example for the JURA app or for the [analysis tool](analysis.md):

1. *Settings › Devices & services › JURA Coffee Machines* › menu (⋮) › *Disable*.
2. Use the other device.
3. Enable the entry again. The integration connects within a minute and reads all values again.

## Statistics take long

Reading the product counters can take 20 seconds or more after the request. That is the machine, not the receiver. Maintenance values are read right after the product counters.
