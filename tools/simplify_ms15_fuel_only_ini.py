#!/usr/bin/env python3
"""Hide obsolete spark/racing tuning UI without changing calibration pages.

Preserves all page offsets, scalar definitions, table layouts, signature,
firmware protocols, and fuel/AFR/idle/fan editor definitions. NOT a build.
"""
from pathlib import Path
import re
import sys

HIDE_SUBMENUS = {
    # Ignition-only / decoder user-facing controls.
    'codebase', 'wheeldecoder', 'sparksettings', 'sparktbl', 'sparktbl2',
    'sparkt2', 'idleadvance', 'knock', 'iatcltig', 'dwellsettings',
    'wheelsim', 'splittbl', 'oddwheel', 'sparkmap', 'sparkmap2', 'splitmap',
    # Unused racing features; keep fuel table and protection choices.
    'launchsettings', 'traction', 'traction2', 'hardlim',
    'boostmap1', 'boostmap2', 'boostmap3',
    'shelp1','shelp2','shelp3','shelp4','shelp5','fhelp5',
    'chelp1','chelp4','chelp5',
}


def transform(ini: str) -> str:
    eol = '\r\n' if '\r\n' in ini else '\n'
    lines = ini.splitlines(keepends=True)
    out = []
    menu = ''
    removed = set()
    in_menu_section = False
    for line in lines:
        text = line.strip()
        if re.match(r'^\[Menu\]$',text,re.I):
            in_menu_section = True
        elif re.match(r'^\[[^]]+\]$',text):
            in_menu_section = False
        if in_menu_section:
            match_menu = re.match(r'^menu\s*=\s*"([^"]+)"',text,re.I)
            if match_menu:
                menu = match_menu.group(1)
                if 'Spar&k' in menu:
                    line = '; MS1.5 fuel-only: ignition menu physically removed from firmware\n'.replace('\n',eol)
            if 'Spar&k' in menu:
                # Hide every entry under the obsolete Spark menu, not just
                # entries whose individual titles mention the word spark.
                if re.match(r'^subMenu\s*=',text,re.I):
                    line = '; MS1.5 FUEL ONLY hidden: '+line.lstrip()
            else:
                m=re.match(r'^subMenu\s*=\s*([A-Za-z_][\w]*)\b',text,re.I)
                if m and m.group(1).lower() in HIDE_SUBMENUS:
                    removed.add(m.group(1).lower())
                    line = '; MS1.5 FUEL ONLY hidden: '+line.lstrip()
        out.append(line)
    assert {'codebase','sparkmap','sparkmap2','hardlim','launchsettings','wheeldecoder'} <= removed, removed
    result=''.join(out)
    # Existing matching TunerStudio data definition is an ABI: no edits to
    # page sizes, scalar or array locations, conversion, or firmware signature.
    def data_section(text):
        return text.split('[Constants]',1)[1].split('[Menu]',1)[0]
    assert data_section(result)==data_section(ini)
    assert 'dialog = ms15FanControl' in result
    assert 'subMenu = ms15FanControl' in result
    assert 'subMenu = idleControl' in result
    assert 'subMenu = veTable1Tbl' in result
    assert 'subMenu = afrTable1Tbl' in result
    assert 'subMenu = RevLimiterS' in result
    return result


def main():
    path=Path(sys.argv[1]);t=path.read_bytes().decode('latin-1')
    path.write_bytes(transform(t).encode('latin-1'))
    print('Removed spark/racing menu entry points. INI memory and data layout retained.')

if __name__=='__main__':main()