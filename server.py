"""Compatibility entry point for clients configured to run server.py."""

from caxa_mcp import server as _server

main = _server.main


def __getattr__(name):
    return getattr(_server, name)


if __name__ == "__main__":
    main()
