import os
from mcp.server.fastmcp import FastMCP
from .wal_manager import PostgresWalManager

def create_mcp_server(name: str = "Botmartz Postgres WAL Checkpointer") -> FastMCP:
    """Creates an MCP tool server exposing state checkpointing and Saga rollback tools."""
    mcp = FastMCP(name)
    wal = PostgresWalManager()

    @mcp.tool()
    def checkpoint_state(
        session_id: str,
        step_index: int,
        node_name: str,
        state_json: str,
        compensating_action_json: str = ""
    ) -> str:
        """
        Records a deterministic state transition checkpoint for an autonomous AI agent into PostgreSQL WAL.
        """
        import json
        wal.init_schema()
        payload = json.loads(state_json)
        comp = json.loads(compensating_action_json) if compensating_action_json else None
        cp_id = wal.record_checkpoint(session_id, step_index, node_name, payload, comp)
        return json.dumps({"status": "success", "checkpoint_id": cp_id, "node": node_name})

    @mcp.tool()
    def get_latest_checkpoint(session_id: str) -> str:
        """
        Retrieves the latest verified checkpoint state for an active agent conversation or session.
        """
        import json
        res = wal.get_latest_checkpoint(session_id)
        if not res:
            return json.dumps({"status": "not_found", "session_id": session_id})
        return json.dumps({"status": "success", "data": res})

    @mcp.tool()
    def rollback_session(session_id: str) -> str:
        """
        Executes automated Saga compensating transactions in reverse chronological order when an agent task fails.
        """
        import json
        reversions = wal.execute_saga_rollback(session_id)
        return json.dumps({"status": "rolled_back", "reversions_count": len(reversions), "details": reversions})

    return mcp

if __name__ == "__main__":
    server = create_mcp_server()
    server.run()
