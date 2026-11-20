# Installation and setup

**English** | [Deutsch](installation.de.md) · [Back to the overview](../README.md)

Before you start, check the [requirements](../README.md#requirements): Smart Connect module on the machine, Bluetooth in Home Assistant (directly or through an ESPHome Bluetooth proxy).

## Install

### With HACS (Marketplace)

[![](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=textlastig&repository=jura_ha&category=Integration)

1. HACS (Marketplace) › menu › *Custom repositories*.
2. URL `https://github.com/textlastig/jura_ha`, type *Integration* › *Add*.
3. Open "JURA Coffee Machines" › *Download*.
4. Restart Home Assistant.

Updates then appear in Home Assistant like any other update.

### Without HACS

Copy the folder `custom_components/jura` from the [latest release](https://github.com/textlastig/jura_ha/releases/latest) to `custom_components` in your configuration folder, then restart Home Assistant.

### Switching from the original (AlexxIT/Jura)

The original and this fork both use the domain `jura`, so only one of them may be installed.

1. Remove the original in HACS (do **not** delete the integration entry).
2. Install the fork as described above.
3. Restart Home Assistant.

Your existing entry keeps working. Entities and entity IDs stay the same, so history and statistics are kept.

## Set up

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jura)

1. Switch the machine on.
2. *Settings › Devices & services › Add integration › JURA Coffee Machines*.
3. Pick the machine's MAC address.

If no MAC address is offered, Home Assistant currently sees no machine. Check:

- Is the machine on?
- Is the JURA app on your phone closed? While a phone or Home Assistant is connected, the machine does not advertise and cannot be found.
- Is a Bluetooth receiver close enough? See [Bluetooth troubleshooting](troubleshooting.md).

Machines protected by a PIN are not supported.

After the first setup the machine may be off, even when Home Assistant restarts. The integration remembers model and key and shows the last values until the machine is reachable again.

## Option "Read only, no control"

*Settings › Devices & services › JURA Coffee Machines › Configure.* Off by default.

When on, the integration only creates sensors and binary sensors. Buttons (make, refresh statistics), selects, numbers and the connection switch are removed from Home Assistant. Turning the option off creates them again with the same IDs.

Useful when nobody should make coffee through Home Assistant, for example with voice assistants or dashboards shared with others.

## Next steps

- [Entities](entities.md): what the integration creates
- [Dashboard](dashboard.md): ready-made dashboard and daily counters
