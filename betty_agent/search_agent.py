"""Grounded web search tool for general bird questions."""

import os

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# Definition of an agent tool that accesses Grounding with Google Search

# Read the instructions from a file in the same
# directory as this file.
script_dir = os.path.dirname(os.path.abspath(__file__))
instruction_file_path = os.path.join(script_dir, "search-prompt.txt")

with open(instruction_file_path, "r") as f:
    instruction = f.read()

# Model choice: gemini-2.5-flash. Grounded search is a narrow task - read the
# results and summarise them briefly - so the deeper reasoning of 2.5-pro adds
# latency without improving the answer. Flash keeps this nested call fast
# enough that the extra hop is not noticeable to the customer.
search_agent = Agent(
    name="bird_search_agent",
    model="gemini-2.5-flash",
    description=(
        "Answers general knowledge questions about birds using Grounding "
        "with Google Search."
    ),
    instruction=instruction,
    tools=[google_search],
)

# Wrap the agent so the root agent can call it like any other tool.
search_agent_tool = AgentTool(agent=search_agent)