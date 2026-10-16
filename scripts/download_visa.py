"""Explicit opt-in downloader. No download happens during app startup."""
import argparse
import hashlib
import tarfile
import urllib.request
from pathlib import Path

URL='https://amazon-visual-anomaly.s3.us-west-2.amazonaws.com/VisA_20220922.tar'
EXPECTED='2eb8690c803ab37de0324772964100169ec8ba1fa3f7e94291c9ca673f40f362'
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--authorize-download',action='store_true',help='Explicit approval for the multi-GB dataset download')
    args=parser.parse_args()
    if not args.authorize_download: parser.error('Major dataset download requires --authorize-download')
    args.destination.mkdir(parents=True,exist_ok=True)
    archive=args.destination/'VisA_20220922.tar'
    if not archive.exists(): urllib.request.urlretrieve(URL,archive)
    digest=hashlib.sha256()
    with archive.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    if digest.hexdigest()!=EXPECTED: raise RuntimeError('Dataset archive checksum mismatch; extraction refused')
    with tarfile.open(archive) as tar:
        # Python 3.11.8+ provides the data filter; refuse links and traversal explicitly too.
        base=args.destination.resolve()
        for item in tar.getmembers():
            target=(base/item.name).resolve()
            if not target.is_relative_to(base) or item.issym() or item.islnk(): raise ValueError('Unsafe archive member')
        tar.extractall(base,filter='data')
    print('Dataset extracted and checksum verified')
if __name__=='__main__': main()
