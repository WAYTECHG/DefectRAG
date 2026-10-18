"""Preserve completed official experiment assets, without rerunning a model."""
import hashlib
import json
from pathlib import Path
import zipfile
import argparse
from backend.config import ROOT,CATEGORIES

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--experiment',choices=['official_visa_v1','dinov2_highres_v1'],default='official_visa_v1')
    parser.add_argument('--name',default='DefectRAG-official-benchmark-assets.zip')
    args=parser.parse_args()
    if Path(args.name).name!=args.name or not args.name.endswith('.zip'):raise ValueError('Use a ZIP basename')
    source=ROOT/'experiments'/args.experiment
    archive=ROOT.parent/args.name
    if archive.exists():raise FileExistsError('Earlier archive preserved: '+str(archive))
    for category in CATEGORIES:
        receipt=json.loads((source/category/'complete.json').read_text())
        assert receipt['status']=='passed'
        for name,expected in receipt['files'].items():
            assert digest(source/category/name)==expected,(category,name)
    paths=sorted(p for p in source.rglob('*') if p.is_file() and not set(p.relative_to(source).parts)&{'features','maps'})
    manifest={p.relative_to(source).as_posix():digest(p) for p in paths}
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=3) as output:
        for path in paths:output.write(path,'experiments/'+args.experiment+'/'+path.relative_to(source).as_posix())
        output.writestr('BENCHMARK_MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(archive) as output:
        assert output.testzip() is None
        for name,expected in manifest.items():
            assert hashlib.sha256(output.read('experiments/'+args.experiment+'/'+name)).hexdigest()==expected
    receipt={'status':'passed','archive':archive.name,'bytes':archive.stat().st_size,'sha256':digest(archive),
             'categories':len(CATEGORIES),'files':len(paths)+1,'crc_and_hashes':'passed',
             'restore':'Extract into project root; experiments/'+args.experiment+' appears. Do not overwrite newer experiments.',
             'intermediate_caches':'Feature caches/maps retained on the workstation; not duplicated in this artifact',
             'scope':'experimental banks, official split manifests, calibration, predictions, metrics; no source images or user history'}
    archive.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt,indent=2),flush=True)
