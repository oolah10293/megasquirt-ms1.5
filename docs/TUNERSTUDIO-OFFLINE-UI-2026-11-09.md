# TunerStudio MS1.5 offline UI observations — 2026-11-09

**Test status: PARTIAL GUI RENDERING PASS; calibration read/write NOT VERIFIED.** Observations below are from project-owner screenshots during an offline TunerStudio MS Lite session, not from a connected ECU or simulated ECU. Do not interpret the displayed numbers as actual ECU settings.

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

**Verified:** the custom INI loaded far enough to create/open the project and render both dialogs, section titles, labels, and four custom port indicator captions.

**Not verified:** INI value decoding or defaults, consistency of the new 16-bit settings on actual serial page reads, page-9 writes/burn, `.msq` migration, the rest of the dialogs, serial connectivity, stepper behavior, injector timing, or engine safety.

## Next minimum-effort test

1. Without connecting or flashing an ECU, **load a known-compatible, documented initial tune/project calibration** (if available) and reopen the IAC and fan dialogs to distinguish uninitialized offline data from a definition issue. Do not treat arbitrary invented values as a compatible calibration.
2. If the controls remain absurd, audit the original INI's scalar types, endianness, page sizes, any TunerStudio-specific data-size alignment, and the new settings at page-9 offsets 113–117 against the loaded source and supported format.
3. Record each displayed value or parser warning precisely, then test saving/reopening a project offline. Actual ECU read/burn tests require a dedicated, explicitly planned bench procedure.
4. Clean up obsolete indicators separately after functional tuning checks.

**Safety gate:** No hardware/ECU connection, flashing, firmware rebuild, installer, or release was authorized by this GUI-only observation. The current S19 remains an **UNVALIDATED TEST IMAGE — DO NOT FLASH**.

See [tuning-integrated assembly results](TEST-BUILD-TUNING-2026-11-09.md) and [tuning-source mapping](TUNERSTUDIO-WIP-2026-11-09.md).
