"""
mcp-postgres-wal-server
Maintained by Botmartz AI Solutions Private Limited (https://www.botmartz.com)
"""

__version__ = "0.1.0"

from .server import create_mcp_server
from .wal_manager import PostgresWalManager

__all__ = ["create_mcp_server", "PostgresWalManager"]
