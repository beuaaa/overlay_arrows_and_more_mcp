import asyncio
import sys
import traceback
import json
from typing import Any, Dict
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("overlay_arrows_and_more_mcp")

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

@app.list_tools()
async def list_tools():
    try:
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
    except Exception as e:
        print(f"Erreur dans list_tools: {e}", file=sys.stderr)
        return []

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name != "generate_overlay_script":
            raise ValueError(f"Unknown tool: {name}")

        prompt = arguments.get("prompt", "")
        if not prompt:
            return [TextContent(type="text", text="ERROR: No prompt provided")]

        print(f"Génération de code pour: {prompt}", file=sys.stderr)

        # Essayer d'abord OpenAI, puis fallback vers génération basique
        try:
            from openai import AsyncOpenAI
            import os

            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                print("Pas de clé OpenAI, utilisation du générateur basique", file=sys.stderr)
                raise ValueError("No OpenAI key")

            client = AsyncOpenAI(api_key=api_key)

            reply = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            code = reply.choices[0].message.content.strip()
            print(f"Code généré avec OpenAI: {code[:50]}...", file=sys.stderr)
            return [TextContent(type="text", text=code)]

        except Exception as openai_error:
            print(f"Erreur OpenAI: {openai_error}, utilisation du générateur basique", file=sys.stderr)
            code = generate_basic_overlay_code(prompt)
            return [TextContent(type="text", text=code)]

    except Exception as e:
        print(f"Erreur dans call_tool: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return [TextContent(type="text", text=f"ERROR: Could not generate code - {str(e)}")]

def generate_basic_overlay_code(prompt: str) -> str:
    """Génère un code basique sans LLM basé sur des mots-clés simples"""
    try:
        prompt_lower = prompt.lower()

        # Valeurs par défaut
        x, y = 100, 100
        width, height = 200, 100
        thickness = 3
        color = "(255, 0, 0)"  # rouge par défaut
        shape = "oaam.Shape.rectangle"
        sleep_time = 3

        # Détection de forme
        if any(word in prompt_lower for word in ["circle", "ellipse", "oval", "rond"]):
            shape = "oaam.Shape.ellipse"
        elif any(word in prompt_lower for word in ["arrow", "line", "pointer", "flèche", "ligne"]):
            shape = "oaam.Shape.arrow"
            width, height = 100, 20

        # Détection de couleur
        if any(word in prompt_lower for word in ["blue", "bleu"]):
            color = "(0, 0, 255)"
        elif any(word in prompt_lower for word in ["green", "vert"]):
            color = "(0, 255, 0)"
        elif any(word in prompt_lower for word in ["yellow", "jaune"]):
            color = "(255, 255, 0)"
        elif any(word in prompt_lower for word in ["black", "noir"]):
            color = "(0, 0, 0)"

        # Génération du code
        code = f"""import overlay_arrows_and_more as oaam
import time

main_overlay = oaam.Overlay()
main_overlay.add(geometry={shape}, x={x}, y={y}, width={width}, height={height}, thickness={thickness}, color={color})
main_overlay.refresh()
time.sleep({sleep_time})
main_overlay.clear_all()
main_overlay.refresh()"""

        print(f"Code généré en mode basique: {code[:50]}...", file=sys.stderr)
        return code

    except Exception as e:
        print(f"Erreur dans generate_basic_overlay_code: {e}", file=sys.stderr)
        return f"ERROR: Could not generate basic code - {str(e)}"

async def main():
    try:
        print("Démarrage du serveur MCP overlay_arrows_and_more", file=sys.stderr)

        # Test des imports au démarrage
        try:
            import overlay_arrows_and_more as oaam
            print("Import overlay_arrows_and_more: OK", file=sys.stderr)
        except ImportError as e:
            print(f"ATTENTION: Import overlay_arrows_and_more échoué: {e}", file=sys.stderr)

        try:
            from openai import AsyncOpenAI
            import os
            if os.environ.get('OPENAI_API_KEY'):
                print("OpenAI disponible avec clé API", file=sys.stderr)
            else:
                print("OpenAI disponible mais pas de clé API", file=sys.stderr)
        except ImportError:
            print("OpenAI non disponible, mode basique uniquement", file=sys.stderr)

        # Utilisation simplifiée de stdio_server
        async with stdio_server() as (read_stream, write_stream):
            print("Serveur stdio créé, démarrage...", file=sys.stderr)
            init_options = app.create_initialization_options()
            await app.run(
                read_stream,
                write_stream,
                initialization_options=init_options
            )

    except Exception as e:
        print(f"Erreur fatale dans main: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise

if __name__ == "__main__":
    try:
        print("Lancement du serveur MCP", file=sys.stderr)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Serveur arrêté par l'utilisateur", file=sys.stderr)
    except Exception as e:
        print(f"Erreur fatale: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)