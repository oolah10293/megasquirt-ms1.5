#!/usr/bin/env python3
"""Source-only 029y4a INI UI cleanup after existing MS1.5 tuning/INI patches.

Calibration ABI and gauges remain unchanged: remove obsolete dialog/menu entry
points, not the underlying flash page definitions needed by older tune files.
"""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simplify_ms15_fuel_only_ini import transform as initial_menu_cleanup

OBSOLETE_DIALOGS = {
    'codebase','sparksettings','sparkt2','dwellsettings','sparkmap',
    'sparkmap2','sparkmap3','wheelsim','wheeldecoder','knock',
    'knockdet','iatcltig','idleadvance','rotarysettings','rotarysplittype',
    'splittbl','oddwheel','tachoutput','boostiat','boostcontrol',
    'launchsettings','waterinj','nossystem','nossystem2',
    'hardlim','ovrboo','traction','traction2','outputs','outputs2',
    'boostmap1','boostmap2','boostmap3',
}
OBSOLETE_MENUS = {'rotary trailing &settings'}

OBSOLETE_HELP = {
    # All these user-help topics describe functionality physically removed
    # from the fuel-only firmware. Remove their definitions, not just menus.
    'fhelp4', 'fhelp5', 'shelp1', 'shelp2', 'shelp3', 'shelp4',
    'shelp5', 'chelp1', 'chelp4', 'chelp5', 'tachohelp',
    'dwellhelp', 'stim4whelp',
}
FUEL_HELP = {
    'fhelp1': '''help = Fhelp1, "MegaSquirt MS1.5 Fuel-Only"
       text = "This controller measures ignition/tach pulses for RPM and injects fuel."
       text = "It does not produce ignition or dwell signals, and has no spark-output selection."
''',
    'fhelp2': '''help = Fhelp2, "Fuel Table Selection"
       text = "Injector channel 1 uses the VE1 map."
       text = "Injector channel 2 may use VE1 or the independent VE2 map."
       text = "When VE3 is enabled and the table-select input goes low, VE3 replaces VE1."
       text = "The configured VE3 switching delay remains active. No nitrous or spark mode is involved."
''',
    'fhelp7': '''help = Fhelp7, "Fuel Rev Limiter"
       text = "The hard RPM threshold cuts both fuel-injection pulse-width commands."
       text = "The soft RPM threshold starts a countdown before a sustained fuel cut."
       text = "The soft delay counts in 0.1 second ticks; no ignition timing or spark outputs are controlled."
''',
    'chelp2': '''help = Chelp2, "Advanced Fuel Configuration"
       text = "Hybrid Alpha-N and MAF settings alter fuel-load calculations."
       text = "Choose settings appropriate to the installed sensors and calibrations."
       text = "Ignition decoder, spark output, and trigger-latency options are retired."
''',
}


def transform_integrated(ini: str) -> str:
    eol = '\r\n' if '\r\n' in ini else '\n'
    lines = ini.splitlines(keepends=True)
    output = []
    section = ''
    prior_menu = ''
    skipped_dialog = ''
    removed_dialogs = set()
    removed_menu_entries = set()

    for line in lines:
        stripped = line.strip()
        if re.match(r'^\[[^]]+\]$',stripped):
            section = stripped.lower()
            skipped_dialog = ''
            prior_menu = ''
        if section == '[menu]':
            m = re.match(r'^menu\s*=\s*"([^"]+)"',stripped,re.I)
            if m:
                prior_menu = m.group(1).lower()
                if prior_menu in OBSOLETE_MENUS:
                    output.append('; MS1.5 removed obsolete rotary menu' + eol)
                    continue
            m = re.match(r'^subMenu\s*=\s*([A-Za-z_]\w*)',stripped,re.I)
            if m:
                name=m.group(1).lower()
                if name in OBSOLETE_DIALOGS or prior_menu in OBSOLETE_MENUS:
                    removed_menu_entries.add(name)
                    output.append('; MS1.5 removed obsolete submenu: '+line.lstrip())
                    continue
        if section == '[userdefined]':
            d = re.match(r'^dialog\s*=\s*([A-Za-z_]\w*)\s*,',stripped,re.I)
            if d:
                skipped_dialog = d.group(1).lower() if d.group(1).lower() in OBSOLETE_DIALOGS else ''
                if skipped_dialog:
                    removed_dialogs.add(skipped_dialog)
                    output.append('; MS1.5 removed obsolete dialog '+skipped_dialog+eol)
                    continue
            if skipped_dialog:
                # Obsolete dialog fields are deleted entirely. Original
                # calibration bits stay present in [Constants] for old tunes.
                continue
            if re.match(r'^dialog\s*=\s*advanced\b',stripped,re.I):
                line = re.sub(r'"[^"]+"','"Advanced Fuel Configuration"',line,count=1)
            if re.match(r'^dialog\s*=\s*RevLimiterS\b',stripped,re.I):
                line = re.sub(r'"[^"]+"','"Fuel Rev Limiting"',line,count=1)
            if re.search(r'\b(?:edismulti|edismultirpm|latency|falsetrig_dis|SoftLimRetard)\b',stripped,re.I):
                # EDIS, ignition timing, or decoder latency setting.
                output.append('; MS1.5 removed spark-only field: '+line.lstrip())
                continue
            if 'NOS on or when Pin6 JP1 low.' in line:
                line=line.replace('NOS on or when Pin6 JP1 low.',
                                  'Table-select input low (former JP1 pin 6).')
            if 'Soft rev limit' in line:
                line=line.replace('Soft rev limit','Soft fuel-cut threshold')
            if 'Soft limit max time' in line:
                line=line.replace('Soft limit max time','Delay to soft fuel cut')
            if 'Hard Rev limit' in line:
                line=line.replace('Hard Rev limit','Hard fuel cut threshold')
        output.append(line)

    result=''.join(output)
    # Strip misleading old spark/nitrous/launch help text, including topics
    # that no longer have visible menus. Replace fuel/VE/rev-limit topics
    # with descriptions of the actual fuel-only execution paths.
    def update_help(match):
        key = match.group(1).lower()
        if key in OBSOLETE_HELP:
            return ''
        if key in FUEL_HELP:
            return FUEL_HELP[key].replace('\n', eol) + eol
        return match.group(0)
    result = re.sub(
        r'(?ims)^help\s*=\s*([A-Za-z0-9_]+)\s*,.*?(?=^help\s*=|^\[CurveEditor\])',
        update_help, result)
    assert {'rotarysettings','nossystem','boostcontrol','knock','launchsettings','hardlim'} <= removed_dialogs,removed_dialogs
    assert 'subMenu = idleControl' in result and 'subMenu = ms15FanControl' in result
    assert 'subMenu = RevLimiterS' in result and 'subMenu = veTable1Tbl' in result
    assert 'subMenu = afrTable1Tbl' in result
    for retired in OBSOLETE_HELP:
        assert not re.search(r'(?im)^\s*help\s*=\s*'+retired+r'\b', result), retired
        assert not re.search(r'(?im)^\s*subMenu\s*=\s*'+retired+r'\b', result), retired
    for help_id in FUEL_HELP:
        assert re.search(r'(?im)^help\s*=\s*'+help_id+r'\b', result), help_id
    # This is deliberately a strict byte-level calibration section guard.
    def constants(t):
        return t.split('[Constants]',1)[1].split('[Menu]',1)[0]
    assert constants(result)==constants(ini)
    menu=result.split('[Menu]',1)[1].split('[UserDefined]',1)[0]
    for line in menu.splitlines():
        m=re.match(r'^\s*subMenu\s*=\s*(\w+)',line,re.I)
        assert not m or m.group(1).lower() not in OBSOLETE_DIALOGS,(m.group(1),line)
    return result


def transform(ini: str)->str:
    return transform_integrated(initial_menu_cleanup(ini))


def main():
    if len(sys.argv)!=2:raise SystemExit('Usage: finalize_ms15_fuel_only_ini.py /path/to/patched/msns-extra.ini')
    p=Path(sys.argv[1]);s=p.read_bytes().decode('latin-1')
    p.write_bytes(transform_integrated(s).encode('latin-1'))
    print('SOURCE ONLY: retired spark/racing dialogs, preserved all calibration bytes')

if __name__=='__main__':main()