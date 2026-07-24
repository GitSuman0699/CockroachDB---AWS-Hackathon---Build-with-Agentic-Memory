"""
Phase 1 — Step 5: MCP Protocol Test
Since cockroachdb-mcp-server v0.2.2 has a startup bug, we verify MCP protocol
support by building a minimal custom MCP server that wraps our proven CockroachDB
connection. This proves the MCP protocol layer works with our stack.

What we test:
1. Start a custom MCP server (SSE transport) that exposes CockroachDB tools
2. Connect to it via MCP client
3. Execute read/write operations through MCP protocol
4. Confirm round-trip works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
import multiprocessing
import time
import psycopg2
from mcp.server.fastmcp import FastMCP
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from app.config import settings

MCP_PORT = 8085


def run_mcp_server(db_url: str, port: int):
    """Run a minimal MCP server that wraps CockroachDB."""
    mcp = FastMCP("mnemosyne-crdb", port=port)

    @mcp.tool()
    def query_db(sql: str) -> str:
        """Execute a SQL query against CockroachDB and return results."""
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute(sql)
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                result = f"Columns: {cols}\n"
                for row in rows:
                    result += f"  {row}\n"
                return result.strip()
            else:
                return f"OK (rowcount: {cur.rowcount})"
        finally:
            cur.close()
            conn.close()

    @mcp.tool()
    def list_tables() -> str:
        """List all user tables in the current database."""
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
            return f"Tables: {tables}" if tables else "No tables found"
        finally:
            cur.close()
            conn.close()

    # Run with SSE transport
    mcp.run(transport="sse")


async def test_mcp():
    """Test MCP protocol with our custom CockroachDB server."""
    print("=" * 60)
    print("P1.5 -- MCP Protocol Test (Custom CockroachDB Server)")
    print("=" * 60)

    # Step 1: Start custom MCP server in a separate process
    print("\n[*] Starting custom MCP server...")
    server_proc = multiprocessing.Process(
        target=run_mcp_server,
        args=(settings.cockroachdb_url, MCP_PORT),
        daemon=True,
    )
    server_proc.start()
    print(f"   Server PID: {server_proc.pid}")

    # Wait for server to be ready
    print(f"   Waiting for server on port {MCP_PORT}...")
    await asyncio.sleep(3)

    if not server_proc.is_alive():
        print("   [X] Server process died!")
        return False

    print("   [OK] Server process is running")

    try:
        # Step 2: Connect via SSE
        sse_url = f"http://localhost:{MCP_PORT}/sse"
        print(f"\n[*] Connecting via SSE to {sse_url}...")

        async with sse_client(sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("   [OK] MCP session initialized")

                # Step 3: List tools
                print("\n[*] Listing MCP tools...")
                tools_result = await session.list_tools()
                tool_names = [t.name for t in tools_result.tools]
                print(f"   Found {len(tool_names)} tools: {tool_names}")

                # Step 4: Test READ
                print("\n[*] Testing READ via MCP (SELECT current_database())...")
                result = await session.call_tool("query_db", {
                    "sql": "SELECT current_database(), current_user;"
                })
                for item in result.content:
                    if hasattr(item, "text"):
                        print(f"   Result: {item.text}")

                # Step 5: Test list_tables
                print("\n[*] Testing list_tables via MCP...")
                result = await session.call_tool("list_tables", {})
                for item in result.content:
                    if hasattr(item, "text"):
                        print(f"   Result: {item.text}")

                # Step 6: Test WRITE
                print("\n[*] Testing WRITE via MCP (CREATE + INSERT + SELECT + DROP)...")

                result = await session.call_tool("query_db", {
                    "sql": "CREATE TABLE IF NOT EXISTS p1_mcp_test (id INT PRIMARY KEY, msg TEXT);"
                })
                print(f"   CREATE: {result.content[0].text}")

                result = await session.call_tool("query_db", {
                    "sql": "INSERT INTO p1_mcp_test VALUES (1, 'hello from MCP protocol');"
                })
                print(f"   INSERT: {result.content[0].text}")

                result = await session.call_tool("query_db", {
                    "sql": "SELECT * FROM p1_mcp_test;"
                })
                print(f"   SELECT: {result.content[0].text}")

                result = await session.call_tool("query_db", {
                    "sql": "DROP TABLE IF EXISTS p1_mcp_test;"
                })
                print(f"   DROP:   {result.content[0].text}")

                # Step 7: Test VECTOR via MCP
                print("\n[*] Testing VECTOR operations via MCP...")
                result = await session.call_tool("query_db", {
                    "sql": "SELECT '[1.0, 2.0, 3.0]'::VECTOR(3);"
                })
                print(f"   VECTOR: {result.content[0].text}")

        print(f"\n{'=' * 60}")
        print("[OK] P1.5 PASSED -- MCP protocol works with CockroachDB")
        print(f"{'=' * 60}")
        return True

    except Exception as e:
        print(f"\n[X] MCP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print("\n[*] Shutting down MCP server...")
        server_proc.terminate()
        server_proc.join(timeout=5)
        if server_proc.is_alive():
            server_proc.kill()
        print("   [OK] Server stopped")


if __name__ == "__main__":
    success = asyncio.run(test_mcp())
    sys.exit(0 if success else 1)
