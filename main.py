"""
PokeAPI Proxy Server (Simple Version)

A FastAPI server that proxies requests to the PokeAPI (https://pokeapi.co/).
This server provides Pokemon knowledge to tool-using LLMs by forwarding requests
to the official PokeAPI and returning the responses.

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Example usage:
    GET /proxy/pokemon/pikachu
    GET /proxy/pokemon-species/1
    GET /proxy/ability/static
    GET /proxy/move/thunder
    GET /proxy/type/electric
    GET /proxy/berry/cheri
    GET /proxy/pokemon?limit=100

This endpoint will forward any path and query string to https://pokeapi.co/api/v2/{path}.

See https://pokeapi.co/docs/v2 for all available endpoints and query options.
"""

import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, HTTPException, Request, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/"

app = FastAPI(
    title="PokeAPI Proxy (Simple)",
    description="A single-endpoint proxy for PokeAPI. Forwards any path/query to https://pokeapi.co/api/v2/{path}. See / for usage instructions.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for *
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()
    logger.info("PokeAPI Proxy server shutting down...")


@app.get("/", tags=["info"])
async def root():
    """
    Welcome to the PokeAPI Proxy Server!

    - Use the `/proxy/{path}` endpoint to forward any request to the PokeAPI.
    - Example: `/proxy/pokemon/pikachu` → https://pokeapi.co/api/v2/pokemon/pikachu
    - Query parameters are forwarded as-is.
    - See [PokeAPI docs](https://pokeapi.co/docs/v2) for all available endpoints.
    """
    return {
        "message": "Welcome to the PokeAPI Proxy Server!",
        "usage": "GET /proxy/{pokeapi_path}",
        "examples": [
            "/proxy/pokemon/pikachu",
            "/proxy/pokemon-species/1",
            "/proxy/ability/static",
            "/proxy/move/thunder",
            "/proxy/type/electric",
            "/proxy/berry/cheri",
            "/proxy/pokemon?limit=100"
        ],
        "pokeapi_docs": "https://pokeapi.co/docs/v2"
    }


@app.get("/proxy/{path:path}", tags=["proxy"], summary="Proxy any PokeAPI v2 endpoint", response_description="Raw response from PokeAPI")
async def proxy_pokeapi(
    request: Request,
    path: str = Path(..., description="The PokeAPI v2 path, e.g. 'pokemon/pikachu' or 'move/15'"),
    version: str = Query(None, description="Filter results to only include data for the specified game version (e.g. 'red')."),
    language: str = Query(None, description="Filter results to only include data for the specified language (e.g. 'en')."),
):
    """
    Proxy any request to the PokeAPI v2.

    - The `{path}` is appended to `https://pokeapi.co/api/v2/`.
    - All other query parameters are forwarded as-is.
    - The named parameters `version` and `language` are used for client-side filtering of the response.
    - These filters apply to fields like `flavor_text_entries`, `names`, `genera`, and similar fields in the response.
    - See [PokeAPI docs](https://pokeapi.co/docs/v2) for all available endpoints and query options.

    Example:
        /proxy/pokemon-species/charmander?version=red&language=en
    """
    url = urljoin(POKEAPI_BASE_URL, path)
    # Remove filter params from query dict before forwarding
    params = dict(request.query_params)
    params.pop("version", None)
    params.pop("language", None)
    logger.info(f"Proxying to: {url} with params: {params} and filters: version={version}, language={language}")
    try:
        response = await client.get(url, params=params)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        elif response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"PokeAPI returned status {response.status_code}")
        data = response.json()
        # If filter params are present, filter the response
        if version or language:
            data = filter_pokeapi_response(
                data,
                version=version,
                language=language
            )
        return JSONResponse(content=data)
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def filter_pokeapi_response(data, version=None, language=None):
    """
    Filter fields in the PokeAPI response by version and language.
    Applies to fields like 'flavor_text_entries', 'names', etc.
    """
    if not isinstance(data, dict):
        return data
    filtered = dict(data)
    # Filter flavor_text_entries
    if 'flavor_text_entries' in filtered and language:
        filtered['flavor_text_entries'] = [
            entry for entry in filtered['flavor_text_entries']
            if entry.get('language', {}).get('name') == language and
               (not version or entry.get('version', {}).get('name') == version)
        ]
    # Filter names
    if 'names' in filtered and language:
        filtered['names'] = [
            entry for entry in filtered['names']
            if entry.get('language', {}).get('name') == language
        ]
    # Filter genera
    if 'genera' in filtered and language:
        filtered['genera'] = [
            entry for entry in filtered['genera']
            if entry.get('language', {}).get('name') == language
        ]
    # Filter version_group_details (for moves, etc.)
    if 'version_group_details' in filtered and version:
        filtered['version_group_details'] = [
            entry for entry in filtered['version_group_details']
            if entry.get('version_group', {}).get('name') == version
        ]
    return filtered


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
