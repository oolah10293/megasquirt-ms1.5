# MS1.5 TunerStudio configuration draft — 2026-11-09

**Historical status when this source draft was written:** This was originally not built. **Update:** A matching tuning-integrated test assembly has since **passed**; see [the current test-build report](TEST-BUILD-TUNING-2026-11-09.md). The INI has now been **partially tested in TunerStudio GUI**: the custom project, IAC dialog and fan dialog render, but their calibration fields show invalid-looking values. **Serial and calibration round-trip remain untested**, and no ECU flashing or release has occurred. See [offline GUI observations](TUNERSTUDIO-OFFLINE-UI-2026-11-09.md). The passing **earlier** test image has the **old 029y3 signature** and does **not** implement the following new configurable motor limits. Do not point a live ECU or the old MS1.5 test image at this new INI.

## Exact input and reproducible patches

Uses the owner's supplied original `029y4a.zip` (archive SHA256 `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`).

- [`../patches/ms15-tuning-ini.patch`](../patches/ms15-tuning-ini.patch) edits **only** the original `msns-extra.ini` to the MS1.5 tuning definition, preserving the other MS1/Extra fuel/AFR tables.
- [`../patches/ms15-tuning-firmware-addendum.patch`](../patches/ms15-tuning-firmware-addendum.patch) changes the existing 32-character firmware signature and text version, and adds five calibration bytes to the **ninth** flash-tuning page.
- [`../firmware/ms15_iac.inc`](../firmware/ms15_iac.inc) now reads step interval, homing length and travel cap from the new page-9 bytes, instead of fixed constants.
- [`../firmware/ms15_defs.inc`](../firmware/ms15_defs.inc) defines the one-time startup initialization bit.
- [`../tools/check_ms15_tuning.py`](../tools/check_ms15_tuning.py) performs static cross-checks of signature/offset/symbol/menu consistency against the subsequently patched source tree.

The source addendum is separate from the original [MS1.5 WIP patch](../patches/ms15-on-029y4a-wip.patch) so the original 029y4a base is never silently changed.

## Matching unique identity — verified in authored source

| Location | Value |
| --- | --- |
| Firmware `Signature:` and INI `[MegaTune].signature` | `MS1.5 format 001 ***************` |
| Firmware `textversion_f` | `MS1.5 TEST rev 0.1 *************` |
| Length | Both exactly **32 bytes**, matching the MS1/Extra historical format |
| TunerStudio INI version | `iniVersion=3.0` to avoid older equivalent-definition precedence |

TunerStudio's developer confirmed that the controller signature selects the INI and `iniVersion` can resolve precedence between INIs with matching signatures: https://www.msextra.com/~msextra/forums/viewtopic.php?t=78642 . The new unique signature is the primary separation from original MS1/Extra.

## New tunable values, all page 9

| INI symbol | Page-9 offset | Flash address | Encoding | Default SOURCE value (not valve-calibrated) |
| --- | ---: | --- | --- | --- |
| `iacStepLowMs` | 113 | `E871` | U08, 2..50 ms INI range | **4 ms** low wait |
| `iacHomeSteps` | 114–115 | `E872–E873` | U16 big endian, 1..510 | **360 closing steps** |
| `iacMaxSteps` | 116–117 | `E874–E875` | U16 big endian, 0..510 | **320 maximum open steps** |

The original table is **113 bytes** and has a fixed 189-byte serial tuning page. The source extension makes it **118 bytes**, still under 189. Static checks of original INI fields found **no overlap** at offsets 113–117. GUI fields were **subsequently observed in TunerStudio offline** (both custom dialogs render), but the displayed values are **not valid or verified**; see [UI observations](TUNERSTUDIO-OFFLINE-UI-2026-11-09.md).

The motor state machine clamps a zero homing count to one and values above 510 to 510 at startup; a step-low delay below 2 is clamped to 2 milliseconds. Those guardrails are **not evidence that 510 steps or 2 ms are mechanically/electrically safe for this GM valve**.

## Position tuning: retain meaningful existing 029y4a values

Previously `idlefreq` on page 9 offset 11 meant *PWM actuator frequency*, but the old closed-loop algorithm still uses that byte as an **upper bound for `idleDC`**. The new INI calls it `iacDemandLimit` (max **command units**), not motor pulse speed. This is **essential**: relabeling it step frequency would be misleading.

The `idleDC` realtime serial byte is still **a 0–255 demand value**, not the actual stepper position. The new motor maps demand to **two full steps per unit**, then clamps that requested target by `iacMaxSteps`. We intentionally **do not** display a fabricated motor-position reading; actual commanded position tracking is in reused RAM and is not yet added to the 39-byte serial telemetry packet.

The original warmup position commands, RPM targets, crank position, dashpot, closed-loop control deadband and recovery times remain tied to their original source variables. The INI expresses their changed meaning as **command units**, instead of % PWM duty. The old `pwmIdle` feature bit still chooses between simple temperature on/off and the original warmup/closed-loop idle demand algorithm; it is **not** a motor power enable switch.

## Menus and outputs

- The old PWM valve-frequency menu is replaced with **MS1.5 Stepper IAC** and **IAC Closed-Loop Response**.
- Added a **Cooling Fan (JS2)** dialog retaining the original `efanontemp` / `efanofftemp` calibration values, without the obsolete X2/LED18 selection conditions.
- Hide generic Output1/Output2, water/nitrous, boost and tach-output **GUI entry points** that conflict with the repurposed outputs; **this does NOT guarantee existing saved tunes cannot enable hidden firmware feature bits**. A follow-up runtime config-rejection/tune-migration review remains mandatory.
- Update idle gauges and front-page port indicators to reflect JS0 STEP, JS1 DIR, JS2 fan command, JS3 spare. Raw port-bit telemetry is *not* confirmation of external transistor voltage/polarity.

## Verification completed without new build

1. Source addendum patch **applies** to the original untouched CRLF `msns-extra.asm`.
2. INI patch **applies** to the original untouched CRLF `msns-extra.ini`, producing the same byte-for-byte modified file as the local source draft.
3. Firmware/INI signature strings are both exactly 32 characters.
4. New offsets 113–117 are uniquely allocated, without overlapping original page-9 constants. The inherited conditional declarations deliberately share addresses at lower offsets.
5. New IAC service's approximate branch-span screen reports no out-of-range local branches; this does **not** substitute for CASM08Z assembly or runtime tests.

**Still required:** a separately authorized new test build to check actual compiled signature, code growth, vector/flash safety and serial editing of new page-9 fields; TunerStudio UI test; safe starting tune values and migration from old `.msq`; actual GM IAC and fan electrical validation, and bench injector timing tests.

**No new build, firmware packaging or release has been performed for this step.**
