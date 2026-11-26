"""Connect AURA's existing AI agent to its local MCP server."""

import asyncio
import os
import json
import logging
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aura_tracing import get_trace_id

logger = logging.getLogger("aura.observability")


async def _search_policy_async(question: str) -> dict:
    server_path = Path(__file__).resolve().with_name(
        "aura_mcp_server.py"
    )

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        cwd=str(server_path.parent),
        env={
            key: os.environ[key]
            for key in (
                "OPENAI_API_KEY",
                "AURA_RAG_CACHE_PATH",
                "TIKTOKEN_CACHE_DIR",
            )
            if key in os.environ
        },
    )

    connection_start = time.perf_counter()

    async with stdio_client(params) as (read, write):
        connection_ms = (
            time.perf_counter() - connection_start
        ) * 1000

        logger.info(
            "trace_id=%s operation=mcp_connection "
            "duration_ms=%.2f",
            get_trace_id(),
            connection_ms,
        )

        async with ClientSession(read, write) as session:
            init_start = time.perf_counter()

            await session.initialize()

            init_ms = (
                time.perf_counter() - init_start
            ) * 1000

            logger.info(
                "trace_id=%s operation=mcp_initialize "
                "duration_ms=%.2f",
                get_trace_id(),
                init_ms,
            )

            tool_start = time.perf_counter()

            result = await session.call_tool(
                "lookup_clinic_policy",
                arguments={"question": question},
            )

            tool_ms = (
                time.perf_counter() - tool_start
            ) * 1000

            logger.info(
                "trace_id=%s operation=mcp_tool_execution "
                "duration_ms=%.2f",
                get_trace_id(),
                tool_ms,
            )

            if result.isError:
                raise RuntimeError("MCP policy tool returned an error")

            for item in result.content:
                if item.type == "text":
                    payload = json.loads(item.text)

                    if (
                        isinstance(payload, dict)
                        and isinstance(payload.get("matches"), list)
                    ):
                        return payload

            raise ValueError("Unexpected MCP policy response")


def search_policy_via_mcp(
    question: str,
    trace_id: str | None = None,
) -> dict:
    if trace_id is None:
        trace_id = get_trace_id() or uuid.uuid4().hex
    if not isinstance(question, str) or not question.strip():
        return {"error": "Invalid policy question"}

    start_time = time.perf_counter()
    status = "success"

    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            result = asyncio.run(asyncio.wait_for(_search_policy_async(question), timeout=90.0))
        else:
            with ThreadPoolExecutor(max_workers=1) as executor:
                result = executor.submit(
                    lambda: asyncio.run(asyncio.wait_for(_search_policy_async(question), timeout=90.0))
                ).result()

        if isinstance(result, dict) and result.get("error"):
            status = "error"

        return result

    except Exception:
        status = "error"
        return {
            "error": "Clinic policy search is temporarily unavailable"
        }

    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "trace_id=%s operation=mcp_policy_search "
            "status=%s duration_ms=%.2f",
            trace_id,
            status,
            duration_ms,
        )

