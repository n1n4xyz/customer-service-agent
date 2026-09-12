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

# Model choice: gemini-2.5-flash.
#
# Grounded search is a read-and-summarise task: issue a query, read the
# returned passages, condense them into a short answer and carry the source
# attribution through. It does not need multi-step reasoning, so the extra
# capability of gemini-2.5-pro buys nothing here while roughly doubling the
# latency of a call that is already nested inside the root agent's turn -
# the customer waits for both hops.
#
# gemini-2.5-flash-lite was faster still, but in testing it was less
# consistent at carrying grounding metadata into its answer, sometimes
# returning the facts without naming the sources they came from. Since
# visible attribution is a requirement for this tool, that rules it out.
#
# Flash handles grounding reliably and keeps the nested call fast enough
# that the extra hop is not noticeable.
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