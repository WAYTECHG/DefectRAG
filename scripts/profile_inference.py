"""One bounded serving profile of the existing models; no fitting or threshold changes."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from backend.config import ROOT,Settings
from backend.vision import Detector

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,required=True)
    args=parser.parse_args()
    detector=Detector(Settings())
    report={'method':'Existing calibrated models; 6 original held-out images, 5 warm repetitions each; no training',
            'categories':{},'python':__import__('platform').python_version(),'torch':torch.__version__}
    if torch.cuda.is_available():
        free,total=torch.cuda.mem_get_info()
        report['gpu']={'name':torch.cuda.get_device_name(),'free_mb_before':free/1024**2,'total_mb':total/1024**2}
    for category in ('pcb1','capsules','cashew'):
        rows=json.loads((ROOT/'results'/f'{category}_predictions.json').read_text())['test']
        chosen=[next(r for r in rows if r['label']==label) for label in (0,1)]
        load=time.perf_counter();detector.load(category)
        cold_load=(time.perf_counter()-load)*1000
        elapsed,core=[],[]
        for iteration in range(6):
            for row in chosen:
                started=time.perf_counter()
                with Image.open(args.dataset/row['image']) as im:
                    im.load();result,_=detector.predict(im,category)
                assert abs(result['score']-row['score'])<1e-5
                if iteration:
                    elapsed.append((time.perf_counter()-started)*1000)
                    core.append(result['inference_ms'])
        report['categories'][category]={'samples':len(elapsed),'core_median_ms':float(np.median(core)),
            'core_p95_ms':float(np.percentile(core,95)),'decoded_image_to_result_median_ms':float(np.median(elapsed)),
            'decoded_image_to_result_p95_ms':float(np.percentile(elapsed,95)),'category_load_ms':cold_load,
            'peak_torch_allocated_gpu_mb':result['peak_gpu_mb'],'device':result['device']}
    # Verify the Docker default CPU path also executes actual weights. Small
    # floating-point differences from calibrated CUDA/FP16 scores are expected.
    cpu=Detector(Settings(device='cpu'))
    with Image.open(args.dataset/chosen[0]['image']) as im:
        started=time.perf_counter();result,_=cpu.predict(im,'cashew')
    report['cpu_smoke']={'verdict':result['verdict'],'score':result['score'],'reference_cuda_score':chosen[0]['score'],
                         'absolute_difference':abs(result['score']-chosen[0]['score']),'total_ms':(time.perf_counter()-started)*1000}
    (ROOT/'results'/'serving_profile.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
