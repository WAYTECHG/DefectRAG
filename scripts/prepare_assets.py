"""Copy only existing, selected public model files; never copy credentials or history."""
import argparse
import shutil
import json
from pathlib import Path
from backend.config import ROOT
from backend.vision import sha256

def copy_tree(source,destination,names):
    destination.mkdir(parents=True,exist_ok=True)
    for name in names:
        path=source/name
        if path.is_file(): shutil.copyfile(path,destination/name)
    if (source/'1_Pooling'/'config.json').exists():
        (destination/'1_Pooling').mkdir(exist_ok=True)
        shutil.copyfile(source/'1_Pooling'/'config.json',destination/'1_Pooling'/'config.json')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--encoder',type=Path,required=True)
    parser.add_argument('--embedding',type=Path,required=True)
    args=parser.parse_args()
    copy_tree(args.encoder,ROOT/'models'/'encoder',['config.json','preprocessor_config.json','model.safetensors'])
    copy_tree(args.embedding,ROOT/'models'/'embedding',['config.json','model.safetensors','config_sentence_transformers.json','modules.json','sentence_bert_config.json','special_tokens_map.json','tokenizer_config.json','tokenizer.json','vocab.txt','README.md'])
    checksums={str(p.relative_to(ROOT)).replace('\\','/'):sha256(p) for p in (ROOT/'models').rglob('*') if p.is_file()}
    (ROOT/'models'/'checksums.json').write_text(json.dumps(checksums,indent=2))
    print('Copied cached public model assets, without modifying source files.')
if __name__=='__main__':main()
