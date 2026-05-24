# server.py
import random
#from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP

mcp = FastMCP("demo-server")


# ── Tool 1: Roll N Dice (6-sided) ─────────────────────────
@mcp.tool()
def roll_dice(n: int = 1) -> str:
    """
    Rolls n number of 6-sided dice and returns each result and total.

    Args:
        n: Number of dice to roll (default is 1)
    """
    if n < 1:
        return "❌ Please provide at least 1 die to roll."
    if n > 100:
        return "❌ Maximum 100 dice allowed."

    rolls = [random.randint(1, 6) for _ in range(n)]
    total = sum(rolls)
    rolls_str = ", ".join(str(r) for r in rolls)

    return f"🎲 Rolled {n}d6 → [{rolls_str}] | Total: {total}"


# ── Tool 2: Add Numbers ───────────────────────────────────
@mcp.tool()
def add_numbers(a: float, b: float) -> str:
    """
    Adds two numbers and returns the result.

    Args:
        a: First number
        b: Second number
    """
    result = a + b
    return f"🧮 {a} + {b} = {result}"


if __name__ == "__main__":
    mcp.run()

#mcp inspector
# uv run fastmcp dev main.py
# uv run fastmcp run main.py