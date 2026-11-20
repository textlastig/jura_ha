# Entities

**English** | [Deutsch](entities.de.md) · [Back to the overview](../README.md)

Which entities appear depends on the model's machine file in `resources.zip`. The integration only creates what the machine file defines.

| Kind | Entities |
|---|---|
| Sensors | Total products, count per product (unit "products", in German "Bezüge"), alerts (`ok`/`alert` with the list of active alerts). Products the machine file marks as inactive (e.g. hot water on the WE6) get a counter too, disabled by default: enable it under the device if your machine has the product. |
| Diagnostic | Maintenance counters (cleaning, filter change, descaling, coffee rinse, as far as the machine has them), maintenance percentages, connection |
| Binary sensors | No drip tray, No coffee grounds container, Fill the water tank, Empty the coffee grounds container, Empty the drip tray, Add beans, Clean the machine, Clean the machine soon, Change the filter, Change the filter soon, Filter active, Descale the machine, Descale the machine soon. Machines with milk products also get Rinse the milk system, Clean the milk system, Clean the milk system soon. |
| Control | Product (named as in the JURA app), grinder ratio (e.g. "50% / 50%"), coffee strength, temperature (Low, Normal, High), amounts (water and bypass in ml, milk, milk foam and milk break in seconds), *Make* button, *Refresh statistics* button, connection switch. Not created with the option ["Read only"](installation.md#option-read-only-no-control). |

## Names and IDs

- Names follow the Home Assistant language (English or German).
- Entity IDs do not depend on the language: `<device>_<mac>_<attribute>`, the same as in the original.
- Products and alerts are named as in the JURA J.O.E. app and on the machine display. The machine file gives each product a text number; the names for it come from the app (version 4.6.16).

## When values are read

- Statistics, maintenance and alerts are read every minute while the machine is on and connected.
- When the machine is off, the entities keep their last values.
- The connection switch disconnects Home Assistant only briefly: the next reading (within a minute) connects again. To keep the machine free for another device, disable the integration entry, see [troubleshooting](troubleshooting.md#another-device-cannot-connect).

## Filter

"Filter active" is the machine's own report that it detected a filter cartridge. The WE6 detects a CLARIS Pro Smart via RFID.

- Without a filter the machine reports the filter percentage as "not used" (0xFF). The filter percentage sensor is then unavailable.
- With a filter it is the other way round for descaling: according to the WE6 manual the machine no longer asks for descaling with a CLARIS Pro Smart.
- The RF filter entries are in every machine file, so they do not tell whether a model can detect filters. Only the machine's report does.
- Checked on a WE6 without a filter: "Filter active" is off and the filter percentage is unavailable.

## Hidden while not used

Whatever the machine reports as "not used" (percentage 0xFF) is hidden on the device page, together with its counter, alert and early warning. Without a filter these are: filter percentage, filter changes, "Change the filter", "Change the filter soon".

- They come back as soon as the machine reports a value again.
- Entities you hid yourself stay hidden.
- Hidden entities keep working, for example in automations.

## What cannot be read

Some values the machine shows on its display are not available over Bluetooth on the WE6: water hardness, auto-off timer, daily counter. Details in [Analysis](analysis.md#results-for-the-we6).
