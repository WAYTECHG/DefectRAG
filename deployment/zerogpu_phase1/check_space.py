"""Read-only runtime/log snapshot for the single approved Phase 1 Space."""
import argparse
import json
import time
from pathlib import Path
from huggingface_hub import HfApi
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'development-support/zerogpu-phase1'
REPO = 'Wizzas/DefectRAG'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logs', choices=('build', 'run'))
    args = parser.parse_args()
    api = HfApi()
    runtime = api.get_space_runtime(REPO).raw
    result = {'runtime': runtime, 'commit': api.space_info(REPO).sha}
    (OUT / 'space-runtime.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if args.logs:
        lines = []
        try:
            with requests.get(f'https://huggingface.co/api/spaces/{REPO}/logs/{args.logs}',
                              headers={'Authorization': f'Bearer {api.token or __import__("huggingface_hub").get_token()}'},
                              stream=True, timeout=(15, 12)) as response:
                response.raise_for_status()
                started = time.monotonic()
                for line in response.iter_lines(chunk_size=1):
                    if line:
                        lines.append(line.decode('utf8', errors='replace'))
                    if len(lines) >= 700 or time.monotonic() - started >= 20:
                        break
        except requests.RequestException as exc:
            lines.append(f'Log stream ended: {type(exc).__name__}')
        (OUT / f'space-{args.logs}.log').write_text('\n'.join(lines), encoding='utf8')
        print('\n'.join(lines[-45:]))


if __name__ == '__main__':
    main()
