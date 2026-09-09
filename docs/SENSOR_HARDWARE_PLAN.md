# Harvesta Sensor Hardware Plan

The backend and dashboard are ready for these measurements. Buy hardware only after the software simulator and one test farm work correctly.

## Recommended first pilot

| Need | Recommended pilot hardware | Why |
|---|---|---|
| Gateway | ESP32-S3-DevKitC-1 | Wi-Fi/Bluetooth LE controller with accessible GPIO for a pilot enclosure |
| Air temperature/humidity | Sensirion SHT31 module inside a ventilated radiation shield | Factory-calibrated digital sensor; typical specifications are ±2% RH and ±0.2°C |
| Soil moisture + soil temperature + EC | METER TEROS 12 plus an SDI-12-capable interface/logger | Field-oriented, calibrated VWC/temperature/EC sensor; much more dependable than a cheap exposed capacitive PCB |
| Soil pH | Atlas Scientific EZO-pH circuit, isolated carrier, suitable probe, and calibration solutions | Supports UART/I²C and multi-point calibration; pH requires regular calibration and maintenance |
| Rainfall | Complete tipping-bucket/spoon rain collector with reed-switch output | Produces pulses that an ESP32 can count; mount level and away from obstructions |
| Power | Weatherproof regulated supply; later add solar panel, charge controller, and protected battery | Start on mains/USB during the pilot so power issues do not look like sensor failures |
| Enclosure | IP65 or better enclosure, cable glands, surge/ESD protection, breathable vent for the air sensor | Farm moisture and lightning transients will damage exposed development boards |

Manufacturer references:

- ESP32-S3 DevKitC: `https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html`
- Sensirion SHT31: `https://sensirion.com/products/catalog/SHT31-DIS-B`
- METER TEROS 12: `https://metergroup.com/products/teros-12/`
- Atlas Scientific EZO-pH: `https://atlas-scientific.com/embedded-solutions/ezo-ph-circuit/`
- Davis rain collector example: `https://www.davisnet.com/collections/add-on-sensors/products/aerocone-rain-collector-with-vantage-pro2-mounting-base`

## Do not buy a cheap NPK probe as the first source of fertilizer advice

The API accepts nitrogen, phosphorus, and potassium values, but low-cost multi-parameter “NPK” probes often need soil-specific calibration and independent comparison. For the first pilot, use laboratory soil tests as the reference. Only display continuous NPK readings after comparing the chosen probe against repeated lab samples.

## Connection map

- SHT31 to ESP32-S3: I²C at the module-supported voltage; share ground.
- EZO-pH to ESP32-S3: isolated I²C or UART carrier; keep the high-impedance pH probe cable separated from pumps and noisy power wiring.
- Rain gauge to ESP32-S3: dry-contact/reed-switch digital input with pull-up and software debouncing.
- TEROS 12: SDI-12, 4–15 V supply. Do not connect its signal directly until the interface voltage and level conversion are verified.
- Battery monitoring: use a protected divider/ADC circuit designed for the battery voltage.

Final GPIO numbers depend on the exact purchased breakout boards and enclosure layout. Do not wire by color alone; verify each manufacturer's pin labels and voltage requirements.

## Data flow already supported

```text
Physical sensor → ESP32 firmware → HTTPS POST /api/sensors/ingest
                → device-key verification → Supabase sensor_readings
                → dashboard NPK/moisture cards + Admin Stored Data + AI context
```

Each gateway is registered by the farmer. The raw device key is shown once; only its SHA-256 hash is stored. Rotate a leaked key with `POST /api/sensors/devices/{id}/rotate-key`.

## Pilot sequence

1. Run the software simulator for one week.
2. Build one mains-powered indoor gateway using only ESP32-S3 + SHT31.
3. Compare its readings with a trusted thermometer/hygrometer.
4. Add one soil-moisture sensor at a documented depth and compare gravimetrically or with a trusted reference.
5. Add pH only after calibration buffers and cleaning/storage procedures are ready.
6. Add outdoor enclosure, surge protection, watchdog/reconnect logic, local buffering, and solar power.
7. Deploy multiple soil probes because one point cannot represent an entire field.

The device firmware should buffer readings when the network is down and send timestamps when connectivity returns. Use HTTPS only in production.
