#!/usr/bin/env python3
"""Reproduce the complete MS1.5 fuel-only SOURCE tree; never assemble or build.

Requires the original 029y4a zip, GNU patch, and this repository's source files.
An extracted, disposable source working copy is modified; original source
archive, shipped S19, and all release/workflow files are left untouched.
"""
from pathlib import Path
import argparse
import hashlib
import os
import re
import subprocess
import sys
from zipfile import ZipFile

REPO=Path(__file__).resolve().parents[1]
ORIGINAL_ASM_SHA='a80d055ebed3349c7bc3541a7d1c63c824bed85d290c41638cd659f63aa9e928'
ORIGINAL_S19_SHA='06bbdf436f4be7803c749d9d1d1a6344d8b66e20fb1135d9691bfb499b2486d1'

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    if args.destination.exists():
        raise SystemExit('Refusing to overwrite an existing working directory')
    args.destination.mkdir(parents=True)
    with ZipFile(args.archive) as archive:
        names=archive.namelist()
        a=[n for n in names if n.endswith('/src/msns-extra.asm')]
        s=[n for n in names if n.endswith('/msns-extra.s19')]
        assert len(a)==len(s)==1,(a,s)
        assert sha(archive.read(a[0]))==ORIGINAL_ASM_SHA
        assert sha(archive.read(s[0]))==ORIGINAL_S19_SHA
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
        archive.extractall(args.destination)
        tree=args.destination/a[0].split('/src/')[0]
    source=tree/'src/msns-extra.asm'
    ini=tree/'msns-extra.ini'
    assert source.exists() and ini.exists()
    old_s19=tree/'msns-extra.s19'
    original_image=old_s19.read_bytes()
    for name in ('ms15_defs.inc','ms15_iac.inc','ms15_outputs.inc'):
        buf=(REPO/'firmware'/name).read_text(encoding='utf-8')
        (tree/'src'/name).write_bytes(re.sub(r'\r?\n','\r\n',buf).encode('ascii'))
    for name in ('ms15-on-029y4a-wip.patch',
                 'ms15-tuning-firmware-addendum.patch',
                 'ms15-tuning-ini.patch'):
        result=subprocess.run(['patch','--binary','--forward','-p1','-i',str(REPO/'patches'/name)],cwd=tree,text=True,capture_output=True)
        print(name,result.stdout.strip())
        assert result.returncode==0,(name,result.stdout,result.stderr)
    # Set *pre-transformation fully integrated* sources for independent tests
    # before applying the end-to-end transform to the working copy.
    backup=tree/'src/ms15-integrated-source-preclean.asm'
    backup.write_bytes(source.read_bytes())
    backup_ini=tree/'ms15-integrated-preclean.ini'
    backup_ini.write_bytes(ini.read_bytes())
    sys.path.insert(0,str(REPO/'tools'))
    from remove_ms15_ignition_full import transform as remove_ignition
    from finalize_ms15_fuel_only import transform_integrated as finish_source
    from simplify_ms15_fuel_only_ini import transform as hide_ini
    from finalize_ms15_fuel_only_ini import transform_integrated as finish_ini
    raw=source.read_bytes().decode('latin-1')
    fuel=finish_source(remove_ignition(raw))
    source.write_bytes(fuel.encode('latin-1'))
    ini_raw=ini.read_bytes().decode('latin-1')
    ini.write_bytes(finish_ini(hide_ini(ini_raw)).encode('latin-1'))
    # The original factory S19 is part of the archive. Assert it was not
    # touched, and absolutely never invoke CASM08Z/compile.bat/Win assembler.
    assert old_s19.read_bytes()==original_image
    os.environ['MS15_ORIGINAL_ZIP']=str(args.archive)
    os.environ['MS15_INTEGRATED_ASM']=str(backup)
    os.environ['MS15_INTEGRATED_INI']=str(backup_ini)
    os.environ['MS15_REQUIRE_INTEGRATED']='1'
    for command in (
        [sys.executable,str(REPO/'tools/check_ms15_source.py'),str(tree/'src')],
        [sys.executable,str(REPO/'tools/check_ms15_tuning.py'),str(tree)],
        [sys.executable,'-m','unittest','discover','-s',str(REPO/'tests'),'-p','test_ms15_source_final_cleanup.py','-v'],
    ):
        subprocess.run(command,env=os.environ.copy(),cwd=REPO,check=True)
    # Human-readable audit of suspicious legacy terms in executable source.
    # A symbol's historical name is not proof of ignition functionality:
    # record the exact remaining instructions for expert review instead
    # of blindly deleting useful RPM/fuel-table state.
    live=[]
    sensitive=re.compile(
        r'\b(?:spark\w*|coil\w*|dwell\w*|knock\w*|launch\w*'
        r'|nitrous\w*|nos\w*|boost\w*|tract\w*|shiftlight\w*'
        r'|T2SC1|T2CH1\w*)\b',re.I)
    for n,raw in enumerate(fuel.splitlines(),1):
        code=raw.split(';',1)[0].strip()
        if not code or code.startswith('*'):
            continue
        if sensitive.search(code):
            live.append((n,code))
    print(f'SOURCE AUDIT: {len(live)} active source lines retain historical ignition/racing names')
    for n,code in live[:120]:
        print(f'  residual-source:{n}: {code}')
    if len(live)>120:
        print(f'  ... {len(live)-120} further references; inspect source, not a pass verdict')
    print('SOURCE AUDIT NOTE: unused tuning ABI names and fuel-table trigger names may remain')
    print('PASS: full integrated MS1.5 patches + physical source cleanup + matching INI source checks')
    print('SOURCE ONLY: no assembler, no S19, no firmware image, no release or flash')

if __name__=='__main__':main()