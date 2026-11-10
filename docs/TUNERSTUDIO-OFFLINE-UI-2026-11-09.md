# TunerStudio MS1.5 offline UI observations — 2026-11-09

**Test status: OFFLINE GUI AND SELECTED TUNE-FILE ROUND-TRIP PASS (owner reported); ECU/serial read/write NOT VERIFIED.** Initial screenshots showed uninitialized-looking calibration values; later testing with an adapted offline test tune displayed the expected five IAC/fan values. These are not values read from a connected ECU or proof of safe motor or fan behavior.

## Setup observed

- Windows **TunerStudio MS Lite v3.3.01** showed a project titled `MegaSquirt MS1.5` after the owner selected the extracted custom MS1.5 `.ini`.
- The project-creation wizard advanced through Configuration Settings and Communication Settings with **RS232 Serial Interface** selected. There was no offline selection in the pictured connection-type dropdown; no ECU detection or working serial connection was demonstrated.
- On the main gauge dashboard, the project opened and displayed **Not Connected**. The bottom row included our custom indicators **JS0 STEP low**, **JS1 DIR=0**, **JS2 fan cmd low**, and **JS3 spare low**.
- Legacy dashboard items such as **Launch On**, **NOS/Tables On** and a spark-advance gauge were still present despite the target engine not using those features. These are cosmetic/semantic cleanup candidates; no functioning ECU status was verified.

## Custom-dialog visual checks

### MS1.5 Stepper IAC

- The custom window titled **MS1.5 Stepper IAC** opened.
- Sections visible: stepper positioning warning, **Stepper motor (new MS1.5 page-9 settings)**, **Position commands**, **Warmup positions**, **Closed-loop speed targets**, **Dashpot**.
- The new fields **Inter-step LOW delay**, **Startup closing steps**, and **Maximum opening steps** were visible with editable controls.
- The idle demand algorithm showed **Temp on/off**, and related idle position fields were greyed out. This *may* be consistent with the selected mode; no alternate mode was tested.
- **Problem:** motor calibration fields displayed implausibly large numeric values (millions), rather than plausible step counts or millisecond delays. The settings have **not** been validated by reading their defaults from a functioning ECU or by loading an authenticated tune.

### MS1.5 Fan Relay (JS2 / PTA3)

- The custom window titled **MS1.5 Fan Relay (JS2 / PTA3)** opened.
- Wiring notes and both fan temperature fields displayed.
- **Problem:** **Fan ON** displayed **-40.0 °F**; **Fan OFF** displayed approximately **7,483,688 °F**. These cannot be considered validated fan setpoints.
- The screenshot showed **Burn** and **Close** buttons. There is no evidence of a successful write or connected device.

## Explanation: uncertainty, not diagnosis

The owner recalled a warning about **no tune loaded** when opening the IAC dialog but did not retain its exact wording. An unpopulated offline project is a **plausible** cause of the nonsensical calibration fields. However, these screenshots **do not establish** whether the source is missing project calibration data, an INI offset/type/formatting error, old-firmware tune incompatibility, or something else.

**Initially verified from screenshots:** the custom INI loaded far enough to create/open the project and render both dialogs, section titles, labels, and four custom port indicator captions.

**Update after loading an adapted offline test tune:** the owner reported correctly displayed IAC and fan values, persistence across application restart, and a successful separate tune-file save/reopen test; see the results below.

**Not verified:** real-ECU calibration values, 16-bit data on actual serial page reads, writes/burn, migration of arbitrary existing `.msq` files, other dialogs, serial connectivity, motor behavior, injector timing, or engine safety.

## Subsequent offline tune test — reported PASS

The owner loaded an **offline MS1.5 test tune** adapted from the original 029y4a `default-degF.msq`. This is a diagnostic project/tune, **not** an engine-ready calibration. Its signature was adapted for the MS1.5 custom INI; initial page-9 motor test values were supplied explicitly.

| GUI field | Offline test expectation | Owner-reported result |
| --- | --- | --- |
| Idle demand algorithm | Original setting | `Temp on/off*` |
| Inter-step LOW delay | 4 ms | 4 ms |
| Startup closing steps | 360 | 360 |
| Maximum opening steps | 320 | 320 |
| Fan ON | 194°F | 194°F |
| Fan OFF | 145°F | 145°F |

All **five numeric checks matched** in the owner's TunerStudio display after loading this tune. The owner then reported that closing/reopening TunerStudio preserved those values, and separately confirmed a **Save Tune As** to another `.msq` followed by **Open Tune** successfully restored the same settings. This validates the **reported offline UI file round-trip for these fields**, not ECU flash/page serialization. The saved round-trip `.msq` was not uploaded to the repository for independent byte-level inspection.

**Two import warnings remain** (owner provided exact text):

```text
Warning: MSQ Units Mismatch for afrBins1! Volts found in current configuration, AFR found in MSQ, values were not converted to new units.
Warning: MSQ Units Mismatch for afrBins2! Volts found in current configuration, AFR found in MSQ, values were not converted to new units.
```

These warnings are consistent with the project's then-selected **Narrowband Sensor (Default)** EGO/O₂ configuration (volts) versus AFR units in the adapted tune; this interpretation has **not** yet been independently verified by opening and checking those tables. The warnings specifically say no conversion happened. **Do not assume either AFR table is suitable for real tuning.**

**Interpretation:** the disappearance of the extreme values immediately after loading an offline calibration supports the missing-tune explanation for the initial display problem. It does **not definitively rule out** INI value-format bugs in other fields or actual ECU communication.

## Next tests

1. Before live tuning, select/verify the intended wideband O₂ controller's calibration and check both AFR tables in the TunerStudio project. Resolve the two units-mismatch warnings safely rather than ignoring them.
2. Inspect any remaining custom/legacy dialogs and obsolete indicators as desired; avoid unnecessary GUI changes before functional checks.
3. For the next **bench** milestone, identify the original MS1 hardware, Stim board, serial connection, and IAC motor driver; plan safe ECU communication and timing tests. **Any new firmware build or physical flash requires its own explicit authorization.** No on-engine validation has occurred.

## Historical initial test plan (superseded by results above)

1. Without connecting or flashing an ECU, **load a known-compatible, documented initial tune/project calibration** (if available) and reopen the IAC and fan dialogs to distinguish uninitialized offline data from a definition issue. Do not treat arbitrary invented values as a compatible calibration.
2. If the controls remain absurd, audit the original INI's scalar types, endianness, page sizes, any TunerStudio-specific data-size alignment, and the new settings at page-9 offsets 113–117 against the loaded source and supported format.
3. Record each displayed value or parser warning precisely, then test saving/reopening a project offline. Actual ECU read/burn tests require a dedicated, explicitly planned bench procedure.
4. Clean up obsolete indicators separately after functional tuning checks.

**Safety gate:** No hardware/ECU connection, flashing, firmware rebuild, installer, or release was authorized by this GUI-only observation. The current S19 remains an **UNVALIDATED TEST IMAGE — DO NOT FLASH**.

See [tuning-integrated assembly results](TEST-BUILD-TUNING-2026-11-09.md) and [tuning-source mapping](TUNERSTUDIO-WIP-2026-11-09.md).
