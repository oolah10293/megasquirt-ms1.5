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
                if name in OBSOLETE_DIALOGS or name in OBSOLETE_HELP or prior_menu in OBSOLETE_MENUS:
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
    # The [FrontPage] indicators are the selectable dashboard vocabulary.
    # "indicator" creates a default tile; "indicatorTemplate" adds only a
    # right-click alternative. Keep TunerStudio's built-in connection,
    # datalogging and protocol-error tiles under application control.
    head, front_and_rest = result.split('[FrontPage]', 1)
    front, tail = front_and_rest.split('[RunTime]', 1)
    start = front.index('    ;         =   expression')
    end = front.index(';-------------------------------------------------------------------------------', start)
    legacy = front[start:end]
    for stale in ('"Output3 Off"', '"Launch On"', '"Knocked"',
                  '"NOS/Tables On"', '"LED18 low"'):
        assert stale in legacy, stale
    assert len(re.findall(r'(?m)^\s*indicator\s*=', legacy)) == 12

    # Existing 39-byte serial packet supplies port A/C and engine state.
    # All pin states indicate the MCU's command, not a verified relay load.
    defaults = [
        ('porta & 0b00000001', 'Fuel Pump OFF', 'Fuel Pump ON'),
        ('porta & 0b00100000', 'JS0 STEP low', 'JS0 STEP high'),
        ('porta & 0b00010000', 'JS1 DIR=0', 'JS1 DIR=1'),
        ('porta & 0b00001000', 'JS2 Fan cmd low', 'JS2 Fan cmd high'),
        ('porta & 0b00000100', 'JS3 cmd low', 'JS3 cmd high'),
        ('porta & 0b00000010', 'FIDLE cmd low', 'FIDLE cmd high'),
        ('portc & 0b00000001', 'LED17 low', 'LED17 high'),
        ('portc & 0b00000100', 'LED18 low', 'LED18 high'),
        ('portc & 0b00000010', 'LED19 low', 'LED19 high'),
        ('engine & 0b00000001', 'Engine stopped', 'Engine running'),
        ('engine & 0b00000010', 'Not cranking', 'Cranking'),
        ('floodclear && (( engine & 3 ) != 1)', 'Flood clear OFF', 'FLOOD CLEAR'),
        ('portc & 0b10000000', 'Config OK', 'Config ERROR'),
    ]
    # Alternatives do not consume another one of the 16 visible blocks.
    alternatives = [
        ('engine & 0b00000100', 'ASE OFF', 'Afterstart enrich'),
        ('engine & 0b00001000', 'WUE OFF', 'Warmup enrich'),
        ('engine & 0b00010000', 'TPS accel OFF', 'TPS accel ON'),
        ('engine & 0b00100000', 'TPS decel OFF', 'TPS decel ON'),
        ('engine & 0b01000000', 'MAP accel OFF', 'MAP accel ON'),
    ]
    new_indicators = ['    ; MS1.5 output/status choices; physical pins read as MCU logic states']
    for kind, group in (('indicator', defaults), ('indicatorTemplate', alternatives)):
        for expression, off, on in group:
            colors = ('white, black, red, black' if on == 'Config ERROR'
                      or on == 'FLOOD CLEAR' else 'white, black, green, black')
            new_indicators.append(
                f'    {kind} = {{ {expression} }}, "{off}", "{on}", {colors}')
    front = front[:start] + eol.join(new_indicators) + eol + front[end:]
    result = head + '[FrontPage]' + front + '[RunTime]' + tail

    # Six physical outputs share seven serial-burnable page-9 bytes each.
    # Store exactly 42 new bytes at 118..159, leaving old settings at their
    # original offsets and the page's 189-byte transfer length unchanged.
    src_options=[
        'Disabled', 'RPM above', 'RPM below',
        'Coolant above', 'Coolant below',
        'TPS above', 'TPS below',
        'MAP above', 'MAP below',
        'Battery above', 'Battery below',
        'Engine running', 'Engine cranking',
    ]
    modes=['Disabled','Condition A','A AND B','A OR B']
    cfg_definitions=[]
    output_dialogs=[]
    output_menus=[]
    names=('LED17','LED18','LED19','JS2','JS3','FIDLE')
    fields=(('Mode','mode'),('SourceA','src_a'),('OnA','on_a'),
            ('OffA','off_a'),('SourceB','src_b'),('OnB','on_b'),
            ('OffB','off_b'))
    for index,name in enumerate(names):
        offset=118+index*7
        mode_opts=modes+(['Cooling fan'] if index==3 else [])
        mopts=', '.join('"'+x+'"' for x in mode_opts)
        sopts=', '.join('"'+x+'"' for x in src_options)
        for j,(ui,sym) in enumerate(fields):
            key=f'ms15Out{index}{ui}'
            if j==0:
                decl=f'      {key} = bits, U08, {offset+j}, [0:2], {mopts}'
            elif sym in ('src_a','src_b'):
                decl=f'      {key} = bits, U08, {offset+j}, [0:3], {sopts}'
            else:
                decl=f'      {key} = scalar, U08, {offset+j}, "raw", 1, 0, 0, 255, 0'
            cfg_definitions.append(decl)
        menu_key=f'ms15Output{index}'
        output_menus.append(f'      subMenu = {menu_key}, "{name} Programmable Output", 9')
        active=f'{{ ms15Out{index}Mode > 0 && ms15Out{index}Mode < 4 }}'
        second=f'{{ ms15Out{index}Mode == 2 || ms15Out{index}Mode == 3 }}'
        output_dialogs += [
            f'   dialog = {menu_key}, "{name} Programmable Output", 9',
            '      field = "#Each output evaluates two conditions at up to 10 Hz"',
            '      field = "#Above: ON >= setpoint, OFF <= reset; Below reverses"',
            '      field = "#Units: RPM /100; CLT F+40; MAP kPa; TPS/BATT ADC"',
            f'      field = "Output mode", ms15Out{index}Mode',
            f'      field = "Condition A source", ms15Out{index}SourceA, {active}',
            f'      field = "A turn-on threshold (raw)", ms15Out{index}OnA, {active}',
            f'      field = "A turn-off threshold (raw)", ms15Out{index}OffA, {active}',
            f'      field = "Condition B source", ms15Out{index}SourceB, {second}',
            f'      field = "B turn-on threshold (raw)", ms15Out{index}OnB, {second}',
            f'      field = "B turn-off threshold (raw)", ms15Out{index}OffB, {second}',
            '',
        ]
    assert len(cfg_definitions)==42 and len(output_menus)==6
    cfg_insert=eol+'       ; MS1.5 programmable outputs: six 7-byte records, p9 118..159'+eol
    cfg_insert+=eol.join(cfg_definitions)+eol
    cfg_anchor='       iacMaxSteps   = scalar, U16, 116, "steps", 1, 0, 0, 510, 0'
    assert result.count(cfg_anchor)==1
    result=result.replace(cfg_anchor,cfg_anchor+cfg_insert)
    menu_anchor='subMenu = ms15FanControl, "Cooling Fan (JS2)"'
    assert result.count(menu_anchor)==1
    result=result.replace(menu_anchor,menu_anchor+eol+
        '      ; MS1.5 programmable output controls'+eol+eol.join(output_menus))
    dialog_anchor='      field = "Fan OFF coolant temp", efanofftemp'
    assert result.count(dialog_anchor)==1
    result=result.replace(dialog_anchor,dialog_anchor+eol+eol.join(output_dialogs))
    # The front-page indicator code above deliberately edits no calibration.
    # For the new page-9 fields, byte-exact preservation of all original
    # constants is checked by removing our one appended declaration section.
    def constants(t):
        return t.split('[Constants]',1)[1].split('[Menu]',1)[0]
    assert constants(result).replace(cfg_insert,'')==constants(ini)
    assert result.count('dialog = ms15Output')==6
    assert result.count('subMenu = ms15Output')==6

    assert {'rotarysettings','nossystem','boostcontrol','knock','launchsettings','hardlim'} <= removed_dialogs,removed_dialogs
    assert 'subMenu = idleControl' in result and 'subMenu = ms15FanControl' in result
    assert 'subMenu = RevLimiterS' in result and 'subMenu = veTable1Tbl' in result
    assert 'subMenu = afrTable1Tbl' in result
    for retired in OBSOLETE_HELP:
        assert not re.search(r'(?im)^\s*help\s*=\s*'+retired+r'\b', result), retired
        assert not re.search(r'(?im)^\s*subMenu\s*=\s*'+retired+r'\b', result), retired
    for help_id in FUEL_HELP:
        assert re.search(r'(?im)^help\s*=\s*'+help_id+r'\b', result), help_id
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