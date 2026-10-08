"""Launch every test with isolated HERMES_HOME before Hermes imports."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent

def main():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as home:
        env = dict(os.environ, HERMES_HOME=home, PYTHONDONTWRITEBYTECODE="1")
        for suite in (root / "tests", root / "telegram-approval-explainer" / "tests"):
            request = ["hermes", "--print-runtime-command", "--module", "unittest", "--", "discover", "-s", str(suite), "-v"]
            argv = json.loads(subprocess.check_output(request, env=env))
            subprocess.run(argv, env=env, check=True)

if __name__ == "__main__": main()
