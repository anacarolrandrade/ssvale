from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sofia_chatbot.api import run_server
from sofia_chatbot.config import load_settings


if __name__ == "__main__":
    run_server(load_settings())
