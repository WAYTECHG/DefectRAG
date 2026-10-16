"""Package the already built static showcase; preserve every earlier archive."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='DefectRAG-v2-static.zip')
    args = parser.parse_args()
    if Path(args.name).name != args.name or not args.name.endswith('.zip'):
        raise ValueError('Use a ZIP basename')
    output = ROOT / 'frontend/dist-static'
    if not (output / 'index.html').exists():
        raise RuntimeError('Run npm run build:showcase inside frontend first')
    archive = ROOT.parent / args.name
    if archive.exists():
        raise FileExistsError('Earlier archive preserved: ' + str(archive))
    shutil.copyfile(ROOT / 'deployment/STATIC_SPACE.md', output / 'README.md')
    shutil.copyfile(ROOT / 'LICENSE', output / 'LICENSE')
    shutil.copyfile(ROOT / 'docs/THIRD_PARTY_NOTICES.md', output / 'THIRD_PARTY_NOTICES.md')
    paths = sorted(p for p in output.rglob('*') if p.is_file())
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as zipped:
        for path in paths:
            zipped.write(path, path.relative_to(output).as_posix())
    with zipfile.ZipFile(archive) as zipped:
        if zipped.testzip() is not None:
            raise RuntimeError('Archive CRC failure')
        for path in paths:
            if zipped.read(path.relative_to(output).as_posix()) != path.read_bytes():
                raise RuntimeError('Archived file mismatch')
    receipt = {'status': 'passed', 'archive': str(archive), 'bytes': archive.stat().st_size,
               'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'files': len(paths),
               'mode': 'read-only saved real examples; no server, model download or secret required'}
    archive.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
