"""ASGI entrypoint for VaaniSetu.

Run with:
    uvicorn app:app --host 127.0.0.1 --port 8501
"""

from __future__ import annotations

from api import app


if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("BAIF_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8501")),
        reload=False,
    )
