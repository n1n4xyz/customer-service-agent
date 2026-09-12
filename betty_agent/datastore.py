"""Vertex AI Search tool for Betty's Bird Boutique.

Queries a Vertex AI Search datastore that holds the store's PDF documents
(opening hours, store history, staff profiles).
"""

import os

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1 as discoveryengine

# Definition of a tool that accesses a Vertex AI Search Datastore
#
# This is based on code provided by Google at
# https://cloud.google.com/generative-ai-app-builder/docs/samples/genappbuilder-search
#
# The object definitions aren't available to all IDEs because of Google's ProtoBuf
# implementation, so the IDE may generate a warning, but work fine. I've used
# dicts here instead, but indicated the Class that could be used instead.
# You can see the definitions at
# https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types
#


def search(
    project_id: str,
    location: str,
    engine_id: str,
    search_query: str,
) -> list[str]:
    """Run a query against the Vertex AI Search engine and return raw snippets.

    Args:
        project_id: GCP project that owns the search app.
        location: Location of the search app, usually "global".
        engine_id: ID of the Vertex AI Search app (engine), not the datastore.
        search_query: Natural language query from the customer.

    Returns:
        A list of text passages taken from the indexed documents.
    """
    # For more information, refer to:
    # https://cloud.google.com/generative-ai-app-builder/docs/locations#specify_a_multi-region_for_your_data_store
    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    # Create a client
    client = discoveryengine.SearchServiceClient(client_options=client_options)

    # The full resource name of the search app serving config
    serving_config = f"projects/{project_id}/locations/{location}/collections/default_collection/engines/{engine_id}/servingConfigs/default_config"

    # discoveryengine.SearchRequest
    # Snippets give short answer-shaped passages, extractive answers give the
    # sentences most likely to contain the answer. Both are returned so the
    # agent has enough context to phrase a reply in its own words.
    request = {
        "serving_config": serving_config,
        "query": search_query,
        "page_size": 5,
        # discoveryengine.SearchRequest.ContentSearchSpec
        "content_search_spec": {
            # discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec
            "snippet_spec": {"return_snippet": True},
            # discoveryengine.SearchRequest.ContentSearchSpec.ExtractiveContentSpec
            "extractive_content_spec": {
                "max_extractive_answer_count": 2,
                "max_extractive_segment_count": 1,
            },
        },
        # discoveryengine.SearchRequest.QueryExpansionSpec
        "query_expansion_spec": {"condition": "AUTO"},
        # discoveryengine.SearchRequest.SpellCorrectionSpec
        "spell_correction_spec": {"mode": "AUTO"},
    }

    page_result = client.search(request)

    return _extract_passages(page_result)


def _extract_passages(page_result) -> list[str]:
    """Turn a SearchResponse into a flat list of text passages.

    Helper for search(). Pulls snippets and extractive answers out of the
    nested result structure and labels each passage with its source document
    so the agent can attribute what it says.
    """
    passages: list[str] = []

    for result in page_result:
        document = result.document
        derived = dict(document.derived_struct_data or {})
        source = derived.get("link", document.id)

        for snippet in derived.get("snippets", []):
            text = snippet.get("snippet")
            if text:
                passages.append(f"[{source}] {text}")

        for answer in derived.get("extractive_answers", []):
            text = answer.get("content")
            if text:
                passages.append(f"[{source}] {text}")

        for segment in derived.get("extractive_segments", []):
            text = segment.get("content")
            if text:
                passages.append(f"[{source}] {text}")

    return passages


def search_store_documents(search_query: str) -> list[str]:
    """Search Betty's Bird Boutique store documents.

    Use this tool for questions about the store itself: opening hours, the
    address, the history of the shop, who works there and which birds the
    staff keep. It searches the store's PDF documents and returns passages
    from them.

    Args:
        search_query: The customer's question, or the key terms from it,
            for example "opening hours Thursday" or "who is Betty".

    Returns:
        A list of passages from the store documents. An empty list means
        nothing relevant was found.
    """
    project_id = os.environ.get("DATASTORE_PROJECT_ID", "")
    location = os.environ.get("DATASTORE_LOCATION", "global")
    engine_id = os.environ.get("DATASTORE_ENGINE_ID", "")

    return search(
        project_id=project_id,
        location=location,
        engine_id=engine_id,
        search_query=search_query,
    )