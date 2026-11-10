"""Resume live evidence collection. Does not invent scores or change providers silently."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env
from versioning import build_artifact_version


def matching_runs(version, suite, provider, model):
    version_dir = ROOT / 'artifacts' / 'versions' / version
    hashes = build_artifact_version(version, version_dir / 'system_prompt.md', version_dir / 'tools.yaml')
    found = []
    for path in (ROOT / 'runs').glob('*.json'):
        run = json.loads(path.read_text(encoding='utf-8'))
        identity = {'version': version, 'suite': suite, 'provider': provider, 'model': model,
                    'prompt_hash': hashes.prompt_hash, 'tools_hash': hashes.tools_hash}
        if all(run.get(k) == v for k, v in identity.items()):
            found.append((path, run))
    return sorted(found, key=lambda pair: (pair[1]['summary']['measured_cases'], pair[0].name), reverse=True)


def main():
    load_lab_env(ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', default=os.getenv('LAB_PROVIDER', 'openrouter'),
                        choices=['openrouter', 'openai', 'gemini', 'anthropic', 'ollama'])
    parser.add_argument('--model', default=None)
    parser.add_argument('--interval', type=float, default=3)
    parser.add_argument('--include-baselines', action='store_true', help='Required when changing provider/model for comparable v0-v6 evidence.')
    args = parser.parse_args()
    from providers import make_provider
    model = args.model or os.getenv('LAB_MODEL') or getattr(make_provider(args.provider), 'default_model')
    need_baselines = args.include_baselines or any(
        not matching_runs(f'v{i}', 'base', args.provider, model) for i in (0, 1)
    )
    jobs = [(f'v{i}', 'base', 'eval_base.json') for i in range(0 if need_baselines else 2, 7)]
    jobs += [('v6', 'group', 'eval_group.json'), ('v6', 'extension', 'eval_research_extension.json')]
    for version, suite, dataset in jobs:
        paths = ROOT / 'artifacts' / 'versions' / version
        available = matching_runs(version, suite, args.provider, model)
        expected_total = len(json.loads((ROOT / 'data' / dataset).read_text(encoding='utf-8'))['cases'])
        if available and available[0][1]['summary']['measured_cases'] == expected_total:
            continue
        command = [sys.executable, str(ROOT / 'run_eval.py'), '--provider', args.provider, '--model', model,
                   '--version', version, '--suite', suite, '--eval-cases', str(ROOT / 'data' / dataset),
                   '--system-prompt', str(paths / 'system_prompt.md'), '--tools', str(paths / 'tools.yaml'),
                   '--request-interval', str(args.interval), '--stop-on-provider-error']
        if available:
            command.extend(['--resume', str(available[0][0])])
        subprocess.run(command, cwd=ROOT, check=True)
        available = matching_runs(version, suite, args.provider, model)
        path, run = available[0]
        complete = run['summary']['measured_cases'] == expected_total
        if not complete:
            print('Provider unavailable. Saved evidence; re-run this command after restoring access.')
            return 2
    print(f'All selected evals measured. Next: python chat.py --provider {args.provider} --model {model} --version v6')
    print('Then run: python scripts/build_report.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
