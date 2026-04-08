"""Compatibility wrapper for local `python server.py` runs."""

from sql_env.server import app, main

__all__ = ["app", "main"]


if __name__ == "__main__":
    main()
