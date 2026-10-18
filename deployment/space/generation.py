"""CPU BGE retrieval and bounded genuine Qwen generation on ZeroGPU."""
import os
from pathlib import Path
import json
import time
import atexit
import queue
import subprocess
import sys
import threading
import spaces
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_core.embeddings import Embeddings


class CpuBGE(Embeddings):
    """Exact existing BGE CLS + L2 pooling; no new embedding model."""
    def __init__(self,source):
        source=Path(source)
        pooling=json.loads((source/'1_Pooling/config.json').read_text())
        assert pooling['pooling_mode_cls_token'] and not pooling['pooling_mode_mean_tokens']
        environment=dict(os.environ)
        environment.update(CUDA_VISIBLE_DEVICES='',SPACES_ZERO_GPU='0',USE_TF='0',TOKENIZERS_PARALLELISM='false',DEFECTRAG_LIVE_RAG='0')
        self.process=subprocess.Popen([sys.executable,'-u','-m','deployment.space.embedding_worker','--source',str(source)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding='utf8',env=environment)
        self.responses=queue.Queue()
        def read():
            for line in self.process.stdout:
                self.responses.put(line)
            self.responses.put('{"error":"CPU embedding process stopped"}')
        threading.Thread(target=read,daemon=True).start()
        self.lock=threading.Lock()
        atexit.register(self.close)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()

    def embed_documents(self,texts):
        with self.lock:
            try:
                self.process.stdin.write(json.dumps({'texts':texts})+'\n')
                self.process.stdin.flush()
                response=json.loads(self.responses.get(timeout=45))
            except (OSError,queue.Empty) as exc:
                self.close()
                raise RuntimeError('CPU embedding worker unavailable') from exc
            if 'error' in response:
                raise RuntimeError('CPU embedding worker: '+response['error'])
            return response['vectors']
    def embed_query(self,text):
        return self.embed_documents(['Represent this sentence for searching relevant passages: '+text])[0]


MODEL_ID='Qwen/Qwen3-4B-Instruct-2507'
REVISION='cdbee75f17c01a7cc42f958dc650907174af0554'
TOKENIZER=None
MODEL=None
if os.getenv('SPACES_ZERO_GPU')=='1' and os.getenv('DEFECTRAG_LIVE_RAG')=='1':
    # Download/cache in the Space only. Never place another 8 GB on the laptop.
    TOKENIZER=AutoTokenizer.from_pretrained(MODEL_ID,revision=REVISION)
    MODEL=AutoModelForCausalLM.from_pretrained(MODEL_ID,revision=REVISION,
        dtype=torch.bfloat16,attn_implementation='sdpa').eval().to('cuda')
    MODEL.requires_grad_(False)


@spaces.GPU(duration=45)
@torch.inference_mode()
def generate_text(prompt: str, schema: dict) -> dict:
    if MODEL is None or TOKENIZER is None:
        raise RuntimeError('Cloud generation model is not loaded')
    messages=[{'role':'system','content':'Follow the application instructions. Return only valid JSON matching the supplied schema. No markdown fences or commentary.'},
              {'role':'user','content':prompt+'\nJSON schema: '+json.dumps(schema)}]
    values=TOKENIZER.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_tensors='pt',return_dict=True)
    if values['input_ids'].shape[-1]>4096:
        raise ValueError('Evidence request exceeds the bounded generation context')
    values={key:value.to('cuda') for key,value in values.items()}
    torch.cuda.reset_peak_memory_stats()
    start=time.perf_counter()
    output=MODEL.generate(**values,max_new_tokens=384,do_sample=False,use_cache=True)
    torch.cuda.synchronize()
    text=TOKENIZER.decode(output[0,values['input_ids'].shape[-1]:],skip_special_tokens=True).strip()
    return {'json':text,'metadata':{'provider':'in_space_transformers','model':MODEL_ID,'revision':REVISION,
        'device':torch.cuda.get_device_name(),'zero_gpu':True,'generation_ms':round((time.perf_counter()-start)*1000,2),
        'input_tokens':int(values['input_ids'].shape[-1]),'output_tokens':int(output.shape[-1]-values['input_ids'].shape[-1]),
        'peak_gpu_mb':round(torch.cuda.max_memory_allocated()/1024**2,2)}}
