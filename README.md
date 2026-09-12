# Betty's Bird Boutique - Customer Service Agent

An agent built with Google's Agent Development Kit (ADK) that answers customer
questions for a fictional pet store selling birds and bird supplies. It runs on
Gemini via Vertex AI and pulls its answers from three separate sources rather
than from the model's own knowledge.

The agent does not take orders. Its job is to answer the question and get the
customer into the shop.

## What it does

| Question | Tool | Source |
|---|---|---|
| "How much is millet?" | `get-product-price` | Cloud SQL for MySQL, via MCP Toolbox |
| "When are you open on Thursday?" | `search_store_documents` | Vertex AI Search over the store's PDFs |
| "What do budgies eat?" | `bird_search_agent` | Grounding with Google Search |

Anything outside birds and the store is declined.

## Project structure

```
betty_agent/
  __init__.py          exports the agent for adk web
  agent.py             root agent, session service, tool wiring
  agent-prompt.txt     persona, tool routing rules, guardrails
  datastore.py         Vertex AI Search query and tool function
  search_agent.py      grounded search agent wrapped as an AgentTool
  search-prompt.txt    instructions for the search agent
  .env                 configuration (not in the repo)
docs/
  betty_db.sql         schema and seed data for the product table
  bettys-*.pdf         store documents for the datastore
tools.yaml             MCP Toolbox source and SQL tool definition
requirements.txt
```

## Setup

### Prerequisites

- Python 3.11+
- A GCP project with the Vertex AI, Discovery Engine and Cloud SQL Admin APIs enabled
- A service account with Vertex AI User, Discovery Engine Viewer and Cloud SQL Client roles
- The MCP Toolbox binary from https://github.com/googleapis/mcp-toolbox

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up the database

Create a Cloud SQL for MySQL instance, authorise your IP, then load the schema:

```bash
mysql -h <PUBLIC_IP> -u root -p < docs/betty_db.sql
```

Create a read-only user in the console and grant it access:

```sql
GRANT SELECT ON betty.* TO `betty-app`@'%';
FLUSH PRIVILEGES;
```

### 3. Set up Vertex AI Search

Upload the PDFs in `docs/` to a Cloud Storage bucket, then create a Custom
Search (general) app in AI Applications with an unstructured document data
store pointing at that bucket. Note the engine ID.

### 4. Configure

Create `betty_agent/.env`:

```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

DATASTORE_PROJECT_ID=your-project-id
DATASTORE_LOCATION=global
DATASTORE_ENGINE_ID=your-engine-id

MYSQL_HOST=your-instance-ip
MYSQL_PORT=3306
MYSQL_DATABASE=betty
MYSQL_USER=betty-app
MYSQL_PASSWORD=your-password

TOOLBOX_URL=http://127.0.0.1:5000
```

### 5. Run

The Toolbox server and the agent run in separate terminals.

```bash
# terminal 1
export $(grep -v '^#' betty_agent/.env | xargs)
./toolbox --tools-file "tools.yaml"
```

```bash
# terminal 2
source .venv/bin/activate
adk web
```

Open the URL that `adk web` prints and select `betty_agent`.

## Design notes

**Model choice.** All three tools run on `gemini-2.5-flash`. Pro answered
correctly but was slower and wrote replies that read like a brochure rather
than a shop assistant. Flash-lite was the fastest but gave up after a single
product search term when the first lookup came back empty, where Flash tried
related terms and found something the customer could actually buy.

**Session storage.** `InMemorySessionService`. The agent needs to remember
context within a conversation - "what do they eat?" refers back to the bird
named a turn earlier - but has no requirement to remember anything between
conversations.

**Product search.** The SQL tool uses `LIKE` with wildcards so partial names
match. The prompt tells the agent that the tool's output is the only product
information it has, which stops it from inventing stock the shop does not
carry.

## Known limitations

- Product matching is substring-based, so typos do not match.
- The agent has no notion of the current date and cannot answer "are you open
  today?"
- Occasionally still describes product categories the database does not
  contain, despite the prompt constraint.