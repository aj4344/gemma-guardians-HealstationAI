"""
HealStation AI — Emergency Triage System | entry point
All clinical inference runs locally via Ollama (Gemma 4 gemma4:e2b).
No patient data is transmitted to external servers.

Run: python api.py   (or: uvicorn api:app --host 127.0.0.1 --port 8001)
The application itself lives in the healstation package.
"""

import uvicorn

from config import API_HOST, API_PORT
from healstation.api.app import create_app

app = create_app()


if __name__ == "__main__":
    uvicorn.run("api:app", host=API_HOST, port=API_PORT, reload=False)
