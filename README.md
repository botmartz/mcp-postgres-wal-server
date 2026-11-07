# mcp-postgres-wal-server

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Protocol%202024--11--05-0284C7.svg)](https://modelcontextprotocol.io/)
[![Maintained by Botmartz](https://img.shields.io/badge/Maintained%20by-Botmartz%20AI-0066FF.svg)](https://www.botmartz.com)
[![Research Whitepaper](https://img.shields.io/badge/Architecture%20Spec-LangGraph%20%26%20Postgres%20WAL-00C6FF.svg)](https://www.botmartz.com/insights/human-in-the-loop-multi-agent-systems-langgraph-postgresql-wal)

**`mcp-postgres-wal-server`** is a production **Model Context Protocol (MCP)** server engineered by **[Botmartz AI Solutions](https://www.botmartz.com)**. It supplies autonomous agent frameworks (**LangGraph**, **CrewAI**, **AutoGPT**) with deterministic state persistence, ACID Write-Ahead Logging (WAL) checkpoints in PostgreSQL, and automated Saga pattern rollback transactions.

---

## Architectural Pattern

```
┌─────────────────────────┐       JSON-RPC 2.0        ┌─────────────────────────┐
│  LangGraph Multi-Agent  │ <======================>  │   mcp-postgres-wal-     │
│  StateGraph Supervisor  │      (Tool Request)       │   server (MCP Daemon)   │
└─────────────────────────┘                           └─────────────────────────┘
             │                                                     │
             │ State Failure /                                     ▼
             │ Saga Compensation                      ┌─────────────────────────┐
             └──────────────────────────────────────> │  Neon / PostgreSQL      │
                                                      │  ACID Checkpoint Tables │
                                                      └─────────────────────────┘
```

---

## Exposed MCP Tools

1. **`checkpoint_state`**:
   - Commits an agent node transition with complete variable states and registered compensating actions.
2. **`get_latest_checkpoint`**:
   - Recovers agent context after process restarts, container eviction, or spot instance termination.
3. **`rollback_session`**:
   - Reverses all executed state-changing database or API mutations in reverse chronological order via compensating transactions.

---

## Installation & Running

```bash
git clone https://github.com/botmartz/mcp-postgres-wal-server.git
cd mcp-postgres-wal-server
pip install -e .
```

### Claude Desktop / Antigravity MCP Configuration

Add this server block to your `claude_desktop_config.json` or Antigravity MCP server registry:

```json
{
  "mcpServers": {
    "postgres-wal": {
      "command": "python3",
      "args": ["-m", "mcp_postgres_wal.server"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@ep-forest-1234.us-east-2.aws.neon.tech/neondb?sslmode=require"
      }
    }
  }
}
```

---

## Related Research

Engineered to accompany the technical dissertation: **[Human-in-the-Loop for Multi-Agent Systems: Designing Deterministic State Machines with LangGraph & PostgreSQL WAL](https://www.botmartz.com/insights/human-in-the-loop-multi-agent-systems-langgraph-postgresql-wal)**.

---

## License

Licensed under the Apache License, Version 2.0. Copyright 2026 [Botmartz AI Solutions Private Limited](https://www.botmartz.com).
