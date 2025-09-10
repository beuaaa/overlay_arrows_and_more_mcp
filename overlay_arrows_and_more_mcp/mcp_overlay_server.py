import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import overlay_arrows_and_more as oaam

app = Server("overlay_arrows_and_more_mcp")


# --------------------------------------------------
#  build the strict system prompt (English only)
# --------------------------------------------------
def build_system_prompt() -> str:
    lines = [
        "You are a code generator that produces ONLY valid Python calls to the library overlay_arrows_and_more.",
        "The code must follow this exact pattern:",
        "",
        "import overlay_arrows_and_more as oaam",
        "import time",
        "",
        "main_overlay = oaam.Overlay()",
        "# transparent_overlay = oaam.Overlay(transparency=0.5)  # only if needed",
        "",
        "main_overlay.add(geometry=oaam.Shape.rectangle|ellipse|arrow, x=..., y=..., width=..., height=..., thickness=..., color=(r,g,b))",
        "main_overlay.refresh()",
        "time.sleep(<seconds>)",
        "main_overlay.clear_all()",
        "main_overlay.refresh()",
        "",
        "Rules:",
        "- Use ONLY the constants oaam.Shape.rectangle, oaam.Shape.ellipse, oaam.Shape.arrow.",
        "- Map everyday words (square, circle, line, etc.) to the closest constant above.",
        "- Convert English word-numbers (one, two, twenty) to integers.",
        "- No imports other than oaam and time, no loops, no comments, no screenshot.",
        "- If the request is impossible, answer exactly: ERROR: <one sentence>",
    ]
    return "\n".join(lines)


SYSTEM_PROMPT = build_system_prompt()

# --------------------------------------------------
#  MCP tool
# --------------------------------------------------
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="generate_overlay_script",
            description="Natural language → overlay_arrows_and_more Python script",
            inputSchema={
                "type": "object",
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != "generate_overlay_script":
        raise ValueError(f"Unknown tool: {name}")

    prompt = arguments["prompt"]

    # --- LLM call ----------------------------------------------------------
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    reply = await client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature = 0,
    )
    code = reply.choices[0].message.content.strip()
    return [TextContent(type="text", text=code)]


# --------------------------------------------------
#  entry point
# --------------------------------------------------
async def main():
    async with stdio_server() as (reader, writer):
        await app.run(reader, writer)


if __name__ == "__main__":
    asyncio.run(main())