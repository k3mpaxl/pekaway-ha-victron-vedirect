# Victron VE.Direct — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-%E2%89%A52024.10-blue)](https://www.home-assistant.io/)
[![Validate](https://github.com/k3mpaxl/pekaway-ha-victron-vedirect/actions/workflows/validate.yml/badge.svg)](https://github.com/k3mpaxl/pekaway-ha-victron-vedirect/actions/workflows/validate.yml)

Read live data from **Victron** MPPT solar chargers and SmartShunt/BMV battery monitors via the VE.Direct serial protocol.

> Part of the [Pekaway VAN PI CORE](https://github.com/k3mpaxl/pekaway-vanpi-homeassistant) integration family.

## Features

- **Auto-detection** of device type (MPPT or SmartShunt/BMV)
- **MPPT sensors**: PV voltage/power, battery voltage/current, charge state, yield (today/total), MPPT mode
- **SmartShunt sensors**: state of charge, consumed Ah, time to go, battery voltage/current, energy charged/discharged
- **Binary sensors**: alarm, relay state
- Full Config Flow UI — no YAML needed

## Prerequisites

| | |
|---|---|
| **Hardware** | Victron device with VE.Direct port |
| **Cable** | VE.Direct-to-USB or VE.Direct-to-UART |
| **Raspberry Pi** | `dtoverlay=uart4` (MPPT) and/or `dtoverlay=uart5` (SmartShunt) in `config.txt` when using UART |
| **Home Assistant** | ≥ 2024.10 |

> See the [VAN PI CORE setup guide](https://github.com/k3mpaxl/pekaway-vanpi-homeassistant#2-configtxt-anpassen) for detailed `config.txt` instructions.

## Installation via HACS

1. **HACS** → **Integrations** → three dots → **Custom repositories**
2. Add: `https://github.com/k3mpaxl/pekaway-ha-victron-vedirect` → **Integration**
3. Install **Victron VE.Direct**, restart Home Assistant.

## Setup

1. **Settings → Devices & Services → + Add Integration**
2. Search for **Victron VE.Direct**
3. Enter the serial port (e.g. `/dev/ttyUSB0` or `/dev/serial/by-id/...`)
4. Baud rate defaults to 19200.
5. The device type is detected automatically.

## Migration from v1.x

The older `victron_mppt` and `victron_smartshunt` YAML integrations have been merged into this single integration. Remove old YAML entries and set up via the UI instead.

## Removal

1. **Settings → Devices & Services** → click the integration → **Delete**
2. Optionally uninstall via HACS.

## License

MIT — see [LICENSE](./LICENSE).
