# Commentary: Rapid Prototyping External Knowledge Tools for LLMs

This project is a demonstration of how modern developer tools—like GitHub Copilot and FastAPI—can be used to rapidly prototype a toolserver that provides external knowledge to large language models (LLMs).

## Why This Approach?

- **LLMs are powerful, but not omniscient.** They often need access to up-to-date or specialized data (like Pokémon knowledge) that isn't in their training set.
- **Toolservers** (web APIs with OpenAPI schemas) are a standard way to expose external knowledge to LLMs in a structured, machine-readable way.
- **FastAPI** makes it trivial to spin up a web server with automatic OpenAPI documentation, so LLMs and humans can both discover and use the API easily.
- **GitHub Copilot** (and similar AI coding assistants) can accelerate the process, suggesting code, documentation, and even filtering logic.

## How It Works

- The server exposes a single `/proxy/{path}` endpoint that forwards requests to the [PokeAPI](https://pokeapi.co/), with optional filtering for `version` and `language`.
- The OpenAPI schema is generated automatically by FastAPI, so any tool-using LLM (like those in Open WebUI) can "snap in" this server as a tool and immediately start making structured queries.
- CORS is enabled for [https://bayleaf.chat](https://bayleaf.chat), so web clients can use the proxy directly from the browser.

## Plug-and-Play for LLM Tool Use

- **Open WebUI** and similar LLM frontends can ingest the OpenAPI schema from this server and treat it as a tool, allowing the LLM to make live queries for Pokémon data.
- The filtering parameters (`version`, `language`) are documented in the OpenAPI schema, so the LLM knows how to use them.
- This pattern can be adapted to any external API, not just Pokémon!

## Lessons Learned

- **Rapid prototyping is real:** With Copilot and FastAPI, you can go from idea to working toolserver in under an hour.
- **Documentation is key:** Good docstrings and OpenAPI schemas make it easy for both humans and LLMs to use your tool.
- **Composable knowledge:** By wrapping existing APIs, you can give LLMs access to any knowledge source you want, with minimal glue code.

---

> _This project is both a reference and a template for anyone looking to empower LLMs with external knowledge, quickly and cleanly._
