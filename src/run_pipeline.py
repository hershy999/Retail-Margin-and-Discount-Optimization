import sys
import subprocess
from pathlib import Path

SRC = Path(__file__).resolve().parent
PYTHON = sys.executable


def run(script: str) -> int:
    result = subprocess.run([PYTHON, str(SRC / script)], check=False)
    return result.returncode


def main():
    for script in ["clean_data.py", "validate_data.py", "load_to_postgres.py"]:
        code = run(script)
        if code != 0:
            sys.exit(code)


if __name__ == "__main__":
    main()
