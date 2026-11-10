"""Package only submission sources/evidence, excluding env files, caches and secrets."""
from __future__ import annotations

import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from env_loader import load_lab_env


def submission_files():
    excluded = {'.venv', '.git', '.agents', '.codex', '__pycache__', '.pytest_cache', 'arxiv_papers', 'dist'}
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in relative.parts):
            continue
        if (path.name.startswith('.env') and path.name != '.env.example') or path.name == 'secrets.toml' or path.suffix in {'.pyc', '.log'}:
            continue
        yield path


def main():
    load_lab_env(ROOT)
    files = list(submission_files())
    secrets = [v.encode('utf-8') for k, v in os.environ.items()
               if len(v) >= 8 and any(word in k.upper() for word in ('API_KEY', 'TOKEN', 'SECRET'))]
    findings = [str(p.relative_to(ROOT)) for p in files if any(value in p.read_bytes() for value in secrets)]
    scan = {'files_checked': len(files), 'secret_match_files': findings, 'env_files_included': False}
    history = ROOT / 'analysis' / 'history'
    history.mkdir(parents=True, exist_ok=True)
    (history / 'submission_scan.json').write_text(json.dumps(scan, indent=2), encoding='utf-8')
    if findings:
        print('Refusing package: configured secret found in ' + ', '.join(findings))
        return 1
    output = ROOT / 'dist' / 'research_agent_submission.zip'
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in submission_files():
            archive.write(path, Path('starter_v0') / path.relative_to(ROOT))
        archive.write(ROOT.parent / 'README.md', 'README.md')
        archive.write(ROOT.parent / 'TOOL-SETUP.md', 'TOOL-SETUP.md')
    print(f'Packaged {len(files)} source/evidence files. No .env or configured secrets: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
