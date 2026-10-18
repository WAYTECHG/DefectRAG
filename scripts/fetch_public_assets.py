"""Explicit, optional asset download for a fresh source clone; never fit models."""
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT=Path(__file__).resolve().parents[1]
REPOSITORY='Wizzas/DefectRAG'
REVISION='3717008401fcf9c85612ce6d4c0c77b629c39f53'
PATTERNS=['models/encoder_dinov2/*','models/highres/*','models/embedding/*',
          'models/BGE-LICENSE.txt','samples/*','results/*.json']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list',action='store_true',help='List public asset groups; download nothing')
    args=parser.parse_args()
    print(f'Public Space assets: {REPOSITORY} @ {REVISION}')
    print('Groups: '+', '.join(PATTERNS))
    if args.list:
        return
    # Only immutable public assets are downloaded; application code/config and
    # private runtime are not part of this snapshot selection.
    snapshot_download(REPOSITORY,repo_type='space',revision=REVISION,
                      allow_patterns=PATTERNS,local_dir=ROOT)
    from backend.vision import sha256
    import json
    cards=list((ROOT/'models/highres').glob('*.json'))
    assert len(cards)==12,'All 12 category cards are required'
    for path in cards:
        card=json.loads(path.read_text())
        assert sha256(path.with_suffix('.npz'))==card['bank_sha256']
    print('All 12 bank checksums verified. No fitting, threshold change or GPU experiment.')

if __name__=='__main__':
    main()
