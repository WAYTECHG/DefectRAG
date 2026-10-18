"""CPU-only BGE subprocess. No spaces import or GPU model initialization."""
import argparse
import json
import sys
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer,AutoModel


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    args=parser.parse_args()
    torch.set_num_threads(min(4,torch.get_num_threads()))
    tokenizer=AutoTokenizer.from_pretrained(args.source,local_files_only=True)
    model=AutoModel.from_pretrained(args.source,local_files_only=True,attn_implementation='eager').eval().to('cpu')
    for line in sys.stdin:
        try:
            texts=json.loads(line)['texts']
            if len(texts)>128 or sum(map(len,texts))>160000:
                raise ValueError('Embedding request exceeds bounds')
            vectors=[]
            with torch.inference_mode():
                for start in range(0,len(texts),16):
                    tokens=tokenizer(texts[start:start+16],padding=True,truncation=True,max_length=512,return_tensors='pt')
                    values=model(**tokens).last_hidden_state[:,0]
                    vectors.extend(F.normalize(values.float(),dim=-1).tolist())
            print(json.dumps({'vectors':vectors}),flush=True)
        except Exception as exc:
            print(json.dumps({'error':type(exc).__name__}),flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'error':'embedding_startup_'+type(exc).__name__}),flush=True)
