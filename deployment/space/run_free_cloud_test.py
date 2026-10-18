"""Use existing regular-account free quota; never opt into paid GPU usage."""
import argparse
import os
import subprocess
from huggingface_hub import HfApi, get_token

parser=argparse.ArgumentParser()
parser.add_argument('script',choices=('verify_vision.mjs','verify_rag.mjs'))
args=parser.parse_args()
account=HfApi().whoami()
if account.get('isPro') or account.get('type')!='user':
    raise SystemExit('Automatic authenticated test requires a regular free personal account; paid-credit eligibility not assumed.')
environment=dict(os.environ)
environment['SPACE_HF_TOKEN']=get_token()
print('Using existing regular personal account free ZeroGPU quota; no subscription or credit purchase.',flush=True)
raise SystemExit(subprocess.call(['node','deployment/space/'+args.script,'--cloud'],env=environment))
