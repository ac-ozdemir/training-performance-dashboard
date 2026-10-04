"""Run the full pipeline once from a laptop, using Application Default Credentials.

Usage (from pipeline/): .venv/bin/python -m scripts.run_local
"""

import truststore

# Use the OS trust store locally: this machine's Python CA bundle can't verify some hosts.
truststore.inject_into_ssl()

from main import run  # noqa: E402

if __name__ == "__main__":
    print(run())
