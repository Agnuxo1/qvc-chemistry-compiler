"""Copy pinned submission members out of the notebook's inputs.

SPDX-License-Identifier: Apache-2.0
Run with Python -I: take.py INPUT_ROOT OUTPUT_DIR MEMBERS_JSON [MORE_ROOTS...]
MEMBERS_JSON maps each member name to its sha256 and size. A member is taken from a
plain file whose path ends with the member's name, or else from a ZIP member whose
name ends the same way; only a copy with the pinned size and SHA-256 is kept. Nothing
from an input is executed, and no archive is extracted whole. MORE_ROOTS, such as the folder of
members built in the notebook, are searched the same way.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import zipfile


def digest(stream):
    h = hashlib.sha256()
    while chunk := stream.read(1 << 22):
        h.update(chunk)
    return h.hexdigest()


def ends_with(path_parts, name_parts):
    return tuple(path_parts[-len(name_parts):]) == name_parts


def main():
    root, out, manifest = Path(sys.argv[1]), Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text())
    roots = [root, *map(Path, sys.argv[4:])]
    files = sorted(p for r in roots if r.is_dir() for p in r.rglob('*') if p.is_file())
    zips = [p for p in files if p.suffix == '.zip']
    taken = {}
    for name, pin in manifest.items():
        parts = PurePosixPath(name).parts
        assert not PurePosixPath(name).is_absolute() and '..' not in parts, name
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        for path in files:
            if ends_with(path.parts, parts) and path.stat().st_size == pin['size']:
                with path.open('rb') as stream:
                    if digest(stream) == pin['sha256']:
                        shutil.copyfile(path, target)
                        taken[name] = str(path)
                        break
        for path in zips if name not in taken else []:
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if not ends_with(PurePosixPath(info.filename).parts, parts) or info.file_size != pin['size']:
                        continue
                    # Reading to EOF also checks the member's ZIP CRC.
                    with archive.open(info) as source, target.open('wb') as copy:
                        shutil.copyfileobj(source, copy, length=1 << 20)
                    with target.open('rb') as stream:
                        if digest(stream) == pin['sha256']:
                            taken[name] = f'{path}:{info.filename}'
                            break
                    target.unlink()
            if name in taken:
                break
        if name not in taken:
            raise SystemExit(f'{name}: no input holds SHA-256 {pin["sha256"]}; attach the source its block names')
    print(json.dumps({'status': 'PASS', 'taken': taken}, indent=1))


if __name__ == '__main__':
    main()
