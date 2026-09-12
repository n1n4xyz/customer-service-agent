"""Root agent for Betty's Bird Boutique customer service."""

import os

from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from toolbox_core import ToolboxSyncClient

from .datastore import search_store_documents
from .search_agent import search_agent_tool

# Configure short-term session to use the in-memory service.
# The agent needs to remember facts within a conversation ("what do they
# eat?" refers back to the bird named a turn earlier) but has no requirement
# to remember anything between conversations, so in-memory storage is enough.
session_service = InMemorySessionService()

# Read the instructions from a file in the same
# directory as this agent.py file.
script_dir = os.path.dirname(os.path.abspath(__file__))
instruction_file_path = os.path.join(script_dir, "agent-prompt.txt")

with open(instruction_file_path, "r") as f:
    instruction = f.read()

# Connect to the MCP Toolbox server that exposes the product database.
toolbox_url = os.environ.get("TOOLBOX_URL", "http://127.0.0.1:5000")
db_client = ToolboxSyncClient(toolbox_url)
product_price_tool = db_client.load_tool("get-product-price")

# Set up the tools that we will be using for the root agent
tools = [
    product_price_tool,      # MySQL product prices via MCP Toolbox
    search_store_documents,  # Vertex AI Search over the store's PDFs
    search_agent_tool,       # Grounding with Google Search for bird questions
]

# Create our agent
#
# Model choice: gemini-2.5-flash. The root agent's job is routing - decide
# which of three tools answers the question, carry context across turns, and
# phrase a short reply. All three models were tested on the same sequence
# (store question, follow-up bird question, follow-up product question).
#
# gemini-2.5-pro answered correctly but was noticeably slower and wrote long,
# multi-paragraph replies that read more like a brochure than a shop
# assistant. For a customer waiting on a website, that is the wrong trade.
#
# gemini-2.5-flash-lite was the fastest, but when a product lookup came back
# empty it stopped after a single search term and told the customer the shop
# had nothing. Flash, given the same empty result, tried related terms
# ("pellets", "seeds") and found products the customer could actually buy -
# which is the whole point of the tool.
#
# Flash is the balance point: fast enough to feel responsive, persistent
# enough to be useful.
root_agent = Agent(
    name="bettys_bird_boutique_agent",
    model="gemini-2.5-flash",
    description=(
        "Customer service agent for Betty's Bird Boutique. Answers questions "
        "about the store, its products and prices, and birds in general."
    ),
    instruction=instruction,
    tools=tools,
)