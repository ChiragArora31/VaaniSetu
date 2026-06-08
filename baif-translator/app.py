"""ASGI entrypoint for VaaniSetu.

Run with:
    uvicorn app:app --host 0.0.0.0 --port 8501
"""

from __future__ import annotations

from api import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8501, reload=False)
