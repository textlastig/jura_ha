# JURA Coffee Machines for Home Assistant

**English** | [Deutsch](README.de.md)

Custom integration for [Home Assistant](https://www.home-assistant.io/) that connects JURA coffee machines through the [JURA Smart Connect](https://us.jura.com/en/homeproducts/accessories/SmartConnect-Main-72167) Bluetooth module: read statistics, maintenance status and alerts, and optionally make products.

This is a fork of [AlexxIT/Jura](https://github.com/AlexxIT/Jura). It merges improvements from open pull requests and other forks and adds an option to only read the machine.

![](demo.png)

## What this fork changes

| Change | Source |
|---|---|
| Clean unload, setup retry instead of failure, fresh Bluetooth device on every connection, active scanning (the model is only sent in the scan response) | [madAndroid, AlexxIT/Jura#77](https://github.com/AlexxIT/Jura/pull/77) |
| "Descaling Needed" and "Descaling Soon" sensors, maintenance counters and maintenance percentages, setup while the machine is off with the last known values | [Andrei Marinache, AlexxIT/Jura#41](https://github.com/AlexxIT/Jura/pull/41) |
| "No Beans" sensor, correct key in the statistics command, less log noise | [tidalf, AlexxIT/Jura#59](https://github.com/AlexxIT/Jura/pull/59) |
| **Read only, no control** option, entity names in English and German, product and alert names as in the JURA app, milk system alerts only for machines with a milk system | new in this fork |

Control features are fully included and enabled by default. Entity IDs are the same as in the original, so switching keeps your history and statistics.

## Tested machines

According to the original: [D4](https://github.com/AlexxIT/Jura/issues/49), [E4](https://github.com/AlexxIT/Jura/issues/47), [E6](https://github.com/AlexxIT/Jura/issues/13), E8, ENA8 (with physical buttons), [S8](https://github.com/AlexxIT/Jura/issues/20), [Z8](https://github.com/AlexxIT/Jura/issues/15). This fork runs with a **WE6**. Other models should work as long as their machine file is included in `resources.zip`.

## Installation

[![](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=textlastig&repository=jura_ha&category=Integration)

HACS (Marketplace) › menu › *Custom repositories* › URL `https://github.com/textlastig/jura_ha`, type *Integration* › Add › Download. Then restart Home Assistant.

Without HACS: copy the `custom_components/jura` folder from the [latest release](https://github.com/textlastig/jura_ha/releases/latest) to `custom_components` in your configuration folder.

**Switching from the original:** the original and this fork both use the `jura` domain, so only one of them may be installed. Remove the original in HACS, install the fork, restart. Your existing entry keeps working, entities and IDs stay.

## Configuration

[![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jura)

1. Set up the Home Assistant Bluetooth integration.
2. *Settings › Devices & services › Add integration › JURA Coffee Machines*, pick the MAC address.

The machine has to be on for the first setup. If no MAC address is offered, Home Assistant currently sees no machine: is it on, does Bluetooth work (can the JURA app connect?), and is the receiver close enough? Machines protected by a PIN are not supported.

After that the machine may be off, even when Home Assistant restarts: the integration remembers model and key and shows the last values until the machine is reachable again.

### Option "Read only, no control"

*Settings › Devices & services › JURA Coffee Machines › Configure.* Off by default.

When on, the integration only creates sensors and binary sensors. Buttons (make, refresh statistics), selects, numbers and the connection switch are removed from Home Assistant. Turning it off creates them again with the same IDs. Useful when nobody should make coffee through Home Assistant, for example with voice assistants or shared dashboards.

## Entities

| Kind | Entities |
|---|---|
| Sensors | Total products, count per product (unit "products", in German "Bezüge"), alerts (`ok`/`alert` with the list of active alerts). Products the machine file marks as inactive (e.g. hot water on the WE6) get a counter too, disabled by default: enable it under the device if the machine has it |
| Diagnostic | Maintenance counters (cleaning, filter change, descaling, coffee rinse, as far as the machine has them), maintenance percentages, connection |
| Binary sensors | No drip tray, No coffee grounds container, Fill the water tank, Empty the coffee grounds container, Empty the drip tray, Add beans, Clean the machine, Clean the machine soon, Change the filter, Change the filter soon, Filter active, Descale the machine, Descale the machine soon; machines with milk products also Rinse the milk system, Clean the milk system, Clean the milk system soon. Only alerts the machine file defines are created |
| Control | Product (named as in the JURA app), grinder ratio (e.g. "50% / 50%"), coffee strength, temperature (Low, Normal, High), amounts (water and bypass in ml, milk, milk foam and milk break in seconds), Make button, Refresh statistics button, connection switch |

Names follow the Home Assistant language (English or German); entity IDs do not depend on it (`<device>_<mac>_<attribute>`). Products and alerts are named as in the JURA J.O.E. app and on the machine display: the machine file gives each product a text number, the names for it come from the app (version 4.6.16). Which entities appear depends on the model's machine file. Statistics and alerts are read every minute while the machine is on. The daily counter and the auto-off timer cannot be read over Bluetooth on the WE6 (tested with 1.8.0: statistics page 2 is all zeros even after making a product, setting 0x13 returns no value). The auto-off timer cannot be set either (tested with 1.10.0, therefore removed again in 1.10.1): the machine accepts the JURA app's setting command (`M 13 <value>`) without an error but changes nothing, and the WE6's Smart Connect module does not offer the app's newer text protocol for BlueFrog modules (`@TM:13,…`). A scan of the setting registers 00 to 56 (`M <register>`, 20.11.2026) returned only zeros for every register, including 02, which holds the water hardness on other models. The WE6 machine file has no settings section at all. So water hardness, auto-off timer and daily counter, which the machine shows on its display, cannot be read over Bluetooth on the WE6.

**Filter:** "Filter active" is the machine's own report that it detected a filter cartridge (the WE6 detects a CLARIS Pro Smart via RFID). Without a filter the machine reports the filter percentage as "not used" (0xFF), and the filter percentage sensor is unavailable. With a filter it is the other way round for descaling: according to the WE6 manual the machine no longer asks for descaling with a CLARIS Pro Smart. The RF filter entries are in every machine file, so they do not tell whether a model can detect filters; only the machine's report does. Checked on a WE6 without a filter: "Filter active" is off and the filter percentage is unavailable.

**Hidden while not used:** whatever the machine reports as "not used" (percentage 0xFF) is hidden on the device page, together with its counter, alert and early warning, e.g. without a filter: filter percentage, filter changes, "Change filter", "Change the filter soon". They come back as soon as the machine reports a value again. Entities you hid yourself stay hidden.

## Dashboard and daily counters

![](docs/dashboard.png)

![](docs/dashboard-charts.png)

Ready-made example for a WE6 in [`examples/`](examples/), English (`examples/en/`) and German (`examples/de/`, as in the screenshots). Pick the folder matching your Home Assistant language, because the brew buttons use the product names of the integration.

- `package.yaml`: daily counters (`sensor.jura_we6_*_today`), their helpers, the script `jura_we6_brew` and the automation that sets the daily zero point.
- `dashboard.yaml`: alerts (early warnings "soon" in amber), one-tap brewing with confirmation, custom brewing, maintenance (descaling or filter, whichever the machine uses), products today and total, charts "Today" (every reading) and "Last 7 days" (one value per day). Needs [apexcharts-card](https://github.com/RomRider/apexcharts-card).

Setup:
1. Install apexcharts-card (HACS).
2. Replace `jura_we6_xxxxxxxxxxxx` in both files with your entity prefix (*Settings › Entities*, search "jura").
3. Save `package.yaml` in `/config/packages/` (packages enabled with `homeassistant: packages: !include_dir_named packages`), check the configuration, restart.
4. Create a dashboard (*Settings › Dashboards › Add dashboard › New dashboard from scratch*), open the raw configuration editor and paste `dashboard.yaml`.
5. Other models: remove the products your machine does not have and adapt the product sensors (`sensor.<prefix>_product_*`).

How the daily counters work: the machine only reports totals, and the integration polls them every minute. On the first connection of the day the automation presses *Refresh statistics* at once and stores the totals as the zero point; "today" is the current total minus that zero point. Nothing is interpolated: products made while no reading was possible (Home Assistant, Bluetooth proxy or Bluetooth down, or the machine switched off before the next poll) are counted in the totals but not assigned to any day. Without a reading on a day the daily counters stay at 0.

## Bluetooth

A good Bluetooth receiver matters, see the [Home Assistant list](https://www.home-assistant.io/integrations/bluetooth/). AlexxIT had no stable connection with five adapters (*Unbranded CSR clone detected*); only an adapter with a `CSR8510A10` chip worked reliably.

An [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html) with `active: true` close to the machine works well, for example an M5Stack Atom Lite. The machine sends its model only in the scan response; a receiver that only listens passively is not enough for setup.

## Wi-Fi

The [Wi-Fi module](https://us.jura.com/en/homeproducts/accessories/WiFi-Connect-24160) is not supported and not planned.

## Thanks

- **[AlexxIT](https://github.com/AlexxIT)** for the integration, the protocol work and years of maintenance; this fork would not exist without it.
- **[madAndroid](https://github.com/madAndroid)** (Andrew Stangl) for the fixes to setup, connection and active scanning.
- **[Andrei Marinache](https://github.com/andrei-marinache)** for descaling, maintenance counters and setup while the machine is off.
- **[tidalf](https://github.com/tidalf)** (Cyril Leclerc) for "No Beans" and the statistics command fixes.
- Everyone who tested machines, captured protocols and reported bugs in the original repository.

The fork was merged, extended and tested by [textlastig](https://github.com/textlastig) with the help of [Claude](https://claude.com/claude-code) (Anthropic). Cherry-picked commits keep their original authors; reimplemented parts credit them as co-authors.

## Useful links

- https://lunarius.fe80.eu/blog/tag/bluetooth.html
- https://github.com/Jutta-Proto/protocol-cpp
- https://github.com/Jutta-Proto/protocol-bt-cpp
- https://github.com/franfrancisco9/Jura-Python-BT

## License

The code is licensed under the [MIT License](LICENSE), like AlexxIT's original. The contributions from pull requests AlexxIT/Jura#41, #59 and #77 were submitted to the MIT-licensed original repository and are therefore under the same license. Copyright in those contributions remains with their authors.

**Excluded:** `custom_components/jura/core/resources.zip` contains JURA's machine files (products, settings and alerts per model). They come from JURA, are not covered by the MIT License and are included only to operate this integration, as in the original. The same applies to the product, setting and alert names in `translations/*.json` and `core/texts.json`, which are taken from the JURA J.O.E. app.

JURA and Smart Connect are trademarks of JURA Elektroapparate AG. This project is not affiliated with JURA.
