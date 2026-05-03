import os

from openai import OpenAI

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def get_openai_client() -> OpenAI:
    """Return an OpenAI client with a clear setup error if the key is missing."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or export it before running OpenAI features."
        )

    return OpenAI(api_key=api_key)
