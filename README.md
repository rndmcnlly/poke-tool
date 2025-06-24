# PokeAPI Proxy Server (Simple)

A minimal FastAPI server that proxies requests to the [PokeAPI](https://pokeapi.co/), designed for tool-using LLMs and web clients that need Pokémon knowledge.

## Features
- **Single endpoint**: `/proxy/{pokeapi_path}` forwards any request to the PokeAPI v2.
- **CORS enabled**: Allows requests from [https://bayleaf.chat](https://bayleaf.chat).
- **Client-side filtering**: Use `version` and `language` query parameters to filter fields like `flavor_text_entries`, `names`, and `genera` in the response.
- **OpenAPI docs**: Interactive documentation at `/docs`.

## Example Usage
```
GET /proxy/pokemon/pikachu
GET /proxy/pokemon-species/1
GET /proxy/ability/static
GET /proxy/move/thunder
GET /proxy/type/electric
GET /proxy/berry/cheri
GET /proxy/pokemon?limit=100
GET /proxy/pokemon-species/charmander?version=red&language=en
```

## Filtering
- `version`: Only include data for the specified game version (e.g. `version=red`).
- `language`: Only include data for the specified language (e.g. `language=en`).

These filters apply to fields like `flavor_text_entries`, `names`, and `genera` in the JSON response.

## How it Works
- All requests to `/proxy/{pokeapi_path}` are forwarded to `https://pokeapi.co/api/v2/{pokeapi_path}`.
- All query parameters (except `version` and `language`) are forwarded to PokeAPI.
- The response is filtered on the server if `version` or `language` is provided.

## Running Locally
1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   # or, if using pyproject.toml:
   pip install .
   ```
2. Start the server:
   ```sh
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API docs.

## Deployment
- This project is ready to deploy on any platform that supports FastAPI and Uvicorn (e.g. Fly.io, Render, Heroku, etc).

## License
MIT

## Credits
- [PokeAPI](https://pokeapi.co/) for the Pokémon data
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

> _"Gotta proxy 'em all!"_
