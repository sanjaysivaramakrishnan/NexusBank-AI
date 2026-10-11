"""
NexusBank AI - Entry Point
----------------------------
Run this file to start the multi-agent banking server.

Usage:
    python run.py
"""

import uvicorn

if __name__ == "__main__":
    print()
    print("  +------------------------------------------------------+")
    print("  |                                                      |")
    print("  |   NexusBank AI - Multi-Agent Banking System          |")
    print("  |                                                      |")
    print("  |   Powered by: Gemini + LangGraph + FastAPI           |")
    print("  |   Agents: Supervisor, Customer, Risk, Credit         |")
    print("  |                                                      |")
    print("  |   Open in browser: http://localhost:8000              |")
    print("  |                                                      |")
    print("  +------------------------------------------------------+")
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
