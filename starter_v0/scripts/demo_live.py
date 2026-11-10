"""Feed four scripted turns to the real chat CLI; provider and tool calls stay live."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env
from providers import make_provider

load_lab_env(ROOT)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--provider', default=os.getenv('LAB_PROVIDER', 'openrouter'))
parser.add_argument('--model', default=os.getenv('LAB_MODEL'))
args = parser.parse_args()
args.model = args.model or make_provider(args.provider).default_model
turns = [
    'Theo policy công ty, tweet viral có được coi là fact đã xác nhận không?',
    'Tóm tắt 2 tweet mới nhất giúp mình.',
    'Của @karpathy nhé, giữ đúng 2 tweet.',
    'Gửi nội dung "Đây là bản tin demo" lên Telegram giúp tôi.',
    '/exit',
]
command = [sys.executable, str(ROOT / 'chat.py'), '--provider', args.provider, '--model', args.model,
           '--version', 'v6', '--system-prompt', 'artifacts/versions/v6/system_prompt.md',
           '--tools', 'artifacts/versions/v6/tools.yaml']
subprocess.run(command, cwd=ROOT, input='\n'.join(turns) + '\n', encoding='utf-8', check=True,
               env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
