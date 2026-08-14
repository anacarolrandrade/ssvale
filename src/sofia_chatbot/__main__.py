from sofia_chatbot.api import run_server
from sofia_chatbot.config import load_settings


if __name__ == "__main__":
    run_server(load_settings())
