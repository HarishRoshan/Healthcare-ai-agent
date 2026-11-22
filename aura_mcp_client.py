
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_path = Path(__file__).with_name("aura_mcp_server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        cwd=str(server_path.parent),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Step 1: Establish MCP session
            await session.initialize()
            print("Connected to AURA MCP server!")

            # Step 2: Discover available tools
            tools = await session.list_tools()

            print("\nAvailable MCP tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            # Step 3: Call our existing clinic policy tool
            question = "What is the clinic cancellation policy?"

            result = await session.call_tool(
                "lookup_clinic_policy",
                arguments={"question": question},
            )

            print("\nQuestion:", question)
            print("\nMCP tool response:")

            for item in result.content:
                if item.type == "text":
                    print(item.text)

            if result.isError:
                raise RuntimeError("MCP tool execution failed")


if __name__ == "__main__":
    asyncio.run(main())
