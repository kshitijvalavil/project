"""Local convenience launcher. Tokens are retained outside tracked files."""
import json
import os
from pathlib import Path
import secrets
import app

def main():
    path = Path(__file__).parent/'.data/local-tokens.json'
    path.parent.mkdir(exist_ok=True)
    try:
        with path.open('x') as handle:
            os.chmod(path, 0o600)
            json.dump({name:secrets.token_urlsafe(36) for name in ('BOARD_ADMIN_TOKEN','BOARD_WORKER_TOKEN')},handle)
    except FileExistsError:
        pass
    data = json.loads(path.read_text())
    for name in ('BOARD_ADMIN_TOKEN','BOARD_WORKER_TOKEN'):
        os.environ.setdefault(name, data[name])
    print('Local access tokens are in .data/local-tokens.json. Keep them private.',flush=True)
    app.main()

if __name__ == '__main__':
    main()
