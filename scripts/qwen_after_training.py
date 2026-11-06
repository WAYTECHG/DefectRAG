"""Run every measurement after training, one step at a time, and save a report.

    python -m scripts.qwen_after_training --wait-pid 12345

It waits for the training process to exit, checks that an adapter was saved, then runs:
  1. a check of my_questions.csv
  2. the short-question test (CPU only)
  3. the fine-tuned model on the 100 test questions and on my_questions.csv
  4. the same untouched base model through the same server, for a fair comparison
  5. the original Ollama model on my_questions.csv
  6. comparison tables
Only one heavy process runs at a time. Progress goes to experiments/qwen_lora_v1/pipeline.log.
"""

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

from backend.config import ROOT

OUT = ROOT / "experiments" / "qwen_lora_v1"
LOG = OUT / "pipeline.log"
BASE = OUT / "base_model"
ADAPTER = OUT / "adapter"
ENV = {**os.environ, "PYTHONUTF8": "1", "USE_TF": "0"}


def log(message):
    line = f"{datetime.now():%H:%M:%S}  {message}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def run(name, *args):
    """Run one python module as a step. Returns True on success; never raises."""
    log(f"START {name}")
    started = time.time()
    with (OUT / f"step_{name}.log").open("w", encoding="utf-8") as stream:
        code = subprocess.run(
            [sys.executable, "-m", *args], cwd=ROOT, env=ENV, stdout=stream, stderr=subprocess.STDOUT
        ).returncode
    log(f"{'DONE ' if code == 0 else 'FAILED'} {name} (exit {code}, {(time.time() - started) / 60:.1f} min)")
    return code == 0


def serve(adapter, port=11500):
    """Start the model server and wait until it answers. Returns the process or None."""
    stream = (OUT / f"server_{port}.log").open("w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "scripts.qwen_serve", "--adapter", adapter, "--base", str(BASE), "--port", str(port)],
        cwd=ROOT,
        env=ENV,
        stdout=stream,
        stderr=subprocess.STDOUT,
    )
    for _ in range(120):
        if proc.poll() is not None:
            log(f"FAILED server exited early (exit {proc.returncode})")
            return None
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=3).read()
            log(f"server ready ({adapter})")
            return proc
        except OSError:
            time.sleep(5)
    proc.terminate()
    log("FAILED server did not become ready in 10 minutes")
    return None


def stop(proc):
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    time.sleep(8)  # let the GPU memory be released


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-pid", type=int, default=0, help="process id of the training run to wait for")
    args = parser.parse_args()
    log("pipeline started")
    if args.wait_pid:
        import psutil

        while psutil.pid_exists(args.wait_pid):
            time.sleep(15)
        log("training process has ended")
    if not (ADAPTER / "adapter_model.safetensors").exists():
        log("STOP: no adapter was saved, so training did not finish. See the training window.")
        return
    mine_ok = run("check_mine", "scripts.qwen_eval", "--split", "mine", "--check")
    run("short_questions", "scripts.qwen_short_questions")
    url = "http://127.0.0.1:11500"
    for tag, adapter in (("lora", str(ADAPTER)), ("basehf", "none")):
        proc = serve(adapter)
        if proc is None:
            continue
        try:
            run(f"eval_{tag}_test", "scripts.qwen_eval", "--split", "test", "--tag", tag, "--url", url)
            if mine_ok:
                run(f"eval_{tag}_mine", "scripts.qwen_eval", "--split", "mine", "--tag", tag, "--url", url)
        finally:
            stop(proc)
    if mine_ok:
        run("eval_ollama_mine", "scripts.qwen_eval", "--split", "mine", "--tag", "ollama")
    with (OUT / "pipeline_report.txt").open("w", encoding="utf-8") as report:
        for split, tags in (("test", ["gate50", "basehf", "lora"]), ("mine", ["ollama", "basehf", "lora"])):
            report.write(f"\n===== {split} questions =====\n")
            report.flush()
            subprocess.run(
                [sys.executable, "-m", "scripts.qwen_compare", "--split", split, *tags],
                cwd=ROOT,
                env=ENV,
                stdout=report,
                stderr=subprocess.STDOUT,
            )
    log("ALL DONE: see pipeline_report.txt")


if __name__ == "__main__":
    main()
