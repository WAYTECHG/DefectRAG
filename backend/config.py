from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

# This application uses PyTorch; optional TensorFlow installs must not affect it.
os.environ.setdefault('USE_TF','0')

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
CATEGORIES = ('pcb1', 'capsules', 'cashew')

@dataclass
class Settings:
    root: Path = ROOT
    data: Path = Path(os.getenv('DEFECTRAG_DATA', str(ROOT / 'runtime')))
    encoder: str = os.getenv('DEFECTRAG_ENCODER', str(ROOT / 'models' / 'encoder'))
    device: str = os.getenv('DEFECTRAG_DEVICE', 'auto')
    ollama_url: str = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
    ollama_model: str = os.getenv('OLLAMA_MODEL', 'qwen2.5:3b')
    max_upload: int = 10 * 1024 * 1024
    max_pixels: int = 25_000_000

