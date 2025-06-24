"""
Pokemon Knowledge API for LLMs

A simplified FastAPI server that provides natural language access to Pokemon data.
Each endpoint is designed with clear, semantic function names and detailed docstrings
that serve as natural prompts for LLM tool usage.

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

This API exposes the most commonly needed Pokemon information through
intuitive endpoints that LLMs can easily understand and use.
"""

import logging
from typing import List, Optional, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POKEAPI_BASE = "https://pokeapi.co/api/v2"

app = FastAPI(
    title="Pokemon Knowledge API",
    description="Simple Pokemon data access designed for LLM tool usage",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"]
)

client = httpx.AsyncClient(timeout=30.0)

@app.on_event("shutdown")
async def shutdown():
    await client.aclose()


@app.get("/get_pokemon_info/{name_or_id}")
async def get_pokemon_info(name_or_id: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a specific Pokemon.
    
    Retrieves detailed stats, abilities, types, moves, and characteristics
    for any Pokemon by name or Pokedex number.
    
    Use this when you need to answer questions about:
    - Pokemon stats (HP, Attack, Defense, etc.)
    - Pokemon types and type effectiveness
    - Pokemon abilities and their effects
    - Pokemon moves and movesets
    - Pokemon physical characteristics (height, weight)
    - Pokemon evolution details
    
    Args:
        name_or_id: Pokemon name (like "pikachu") or Pokedex number (like "25")
    
    Returns:
        Complete Pokemon data including stats, types, abilities, and moves
    """
    try:
        # Get basic Pokemon data
        response = await client.get(f"{POKEAPI_BASE}/pokemon/{name_or_id.lower()}")
        if response.status_code == 404:
            raise HTTPException(404, f"Pokemon '{name_or_id}' not found")
        
        pokemon = response.json()
        
        # Get species data for additional info
        species_response = await client.get(pokemon["species"]["url"])
        species = species_response.json()
        
        # Extract key information in a simplified format
        return {
            "name": pokemon["name"].title(),
            "id": pokemon["id"],
            "height": pokemon["height"] / 10,  # Convert to meters
            "weight": pokemon["weight"] / 10,  # Convert to kg
            "types": [t["type"]["name"] for t in pokemon["types"]],
            "abilities": [a["ability"]["name"] for a in pokemon["abilities"]],
            "stats": {
                stat["stat"]["name"]: stat["base_stat"] 
                for stat in pokemon["stats"]
            },
            "generation": species["generation"]["name"],
            "is_legendary": species["is_legendary"],
            "is_mythical": species["is_mythical"],
            "habitat": species["habitat"]["name"] if species["habitat"] else None,
            "color": species["color"]["name"],
            "shape": species["shape"]["name"] if species["shape"] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Pokemon {name_or_id}: {e}")
        raise HTTPException(500, "Failed to retrieve Pokemon data")


@app.get("/compare_pokemon_stats/{pokemon1}/{pokemon2}")
async def compare_pokemon_stats(pokemon1: str, pokemon2: str) -> Dict[str, Any]:
    """
    Compare the battle stats between two Pokemon.
    
    Provides a side-by-side comparison of combat statistics to help
    determine which Pokemon might be stronger in battle or better
    suited for specific roles.
    
    Use this when you need to:
    - Compare two Pokemon for battle effectiveness
    - Determine which Pokemon has higher specific stats
    - Analyze stat differences between Pokemon
    - Help choose between Pokemon for a team
    
    Args:
        pokemon1: First Pokemon to compare (name or ID)
        pokemon2: Second Pokemon to compare (name or ID)
    
    Returns:
        Detailed stat comparison with differences highlighted
    """
    try:
        # Get both Pokemon
        poke1_data = await get_pokemon_info(pokemon1)
        poke2_data = await get_pokemon_info(pokemon2)
        
        # Calculate stat differences
        stat_comparison = {}
        for stat_name in poke1_data["stats"]:
            val1 = poke1_data["stats"][stat_name]
            val2 = poke2_data["stats"][stat_name]
            stat_comparison[stat_name] = {
                poke1_data["name"]: val1,
                poke2_data["name"]: val2,
                "difference": val1 - val2,
                "winner": poke1_data["name"] if val1 > val2 else poke2_data["name"] if val2 > val1 else "tie"
            }
        
        return {
            "pokemon1": {
                "name": poke1_data["name"],
                "types": poke1_data["types"],
                "total_stats": sum(poke1_data["stats"].values())
            },
            "pokemon2": {
                "name": poke2_data["name"], 
                "types": poke2_data["types"],
                "total_stats": sum(poke2_data["stats"].values())
            },
            "stat_comparison": stat_comparison,
            "overall_winner": poke1_data["name"] if sum(poke1_data["stats"].values()) > sum(poke2_data["stats"].values()) else poke2_data["name"]
        }
    except Exception as e:
        logger.error(f"Error comparing {pokemon1} vs {pokemon2}: {e}")
        raise HTTPException(500, "Failed to compare Pokemon")


@app.get("/get_type_effectiveness/{attacking_type}")
async def get_type_effectiveness(attacking_type: str) -> Dict[str, Any]:
    """
    Get type effectiveness information for a Pokemon type.
    
    Shows what types this attacking type is super effective against,
    not very effective against, and has no effect on. Essential
    for battle strategy and type matchup analysis.
    
    Use this when you need to:
    - Plan battle strategies based on type matchups
    - Understand why certain moves are more/less effective
    - Choose the best Pokemon type for specific opponents
    - Learn about Pokemon type relationships
    
    Args:
        attacking_type: The attacking type to analyze (like "fire", "water", "electric")
    
    Returns:
        Complete type effectiveness chart for the given type
    """
    try:
        response = await client.get(f"{POKEAPI_BASE}/type/{attacking_type.lower()}")
        if response.status_code == 404:
            raise HTTPException(404, f"Type '{attacking_type}' not found")
        
        type_data = response.json()
        damage_relations = type_data["damage_relations"]
        
        return {
            "type": attacking_type.title(),
            "super_effective_against": [t["name"] for t in damage_relations["double_damage_to"]],
            "not_very_effective_against": [t["name"] for t in damage_relations["half_damage_to"]],
            "no_effect_against": [t["name"] for t in damage_relations["no_damage_to"]],
            "weak_to": [t["name"] for t in damage_relations["double_damage_from"]],
            "resists": [t["name"] for t in damage_relations["half_damage_from"]],
            "immune_to": [t["name"] for t in damage_relations["no_damage_from"]]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching type {attacking_type}: {e}")
        raise HTTPException(500, "Failed to retrieve type data")


@app.get("/search_pokemon_by_type/{type_name}")
async def search_pokemon_by_type(type_name: str, limit: int = 20) -> Dict[str, List[str]]:
    """
    Find all Pokemon of a specific type.
    
    Returns a list of Pokemon that have the specified type as either
    their primary or secondary type. Useful for building teams or
    finding Pokemon with specific type combinations.
    
    Use this when you need to:
    - Build a team with specific type coverage
    - Find all Pokemon of a particular type
    - Discover Pokemon you might not know about
    - Plan type-themed teams or strategies
    
    Args:
        type_name: The type to search for (like "dragon", "psychic", "fairy")
        limit: Maximum number of Pokemon to return (default 20)
    
    Returns:
        List of Pokemon names that have the specified type
    """
    try:
        response = await client.get(f"{POKEAPI_BASE}/type/{type_name.lower()}")
        if response.status_code == 404:
            raise HTTPException(404, f"Type '{type_name}' not found")
        
        type_data = response.json()
        pokemon_list = [p["pokemon"]["name"].title() for p in type_data["pokemon"][:limit]]
        
        return {
            "type": type_name.title(),
            "pokemon_count": len(type_data["pokemon"]),
            "pokemon": pokemon_list,
            "showing": min(limit, len(type_data["pokemon"]))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching type {type_name}: {e}")
        raise HTTPException(500, "Failed to search Pokemon by type")


@app.get("/get_move_details/{move_name}")
async def get_move_details(move_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a Pokemon move.
    
    Provides comprehensive data about any Pokemon move including
    damage, accuracy, type, effect, and which Pokemon can learn it.
    
    Use this when you need to:
    - Understand what a specific move does
    - Check move power and accuracy for battle planning
    - See which Pokemon can learn a particular move
    - Learn about move effects and status conditions
    
    Args:
        move_name: Name of the move (like "thunderbolt", "fire-blast", "earthquake")
    
    Returns:
        Complete move information including stats and effects
    """
    try:
        response = await client.get(f"{POKEAPI_BASE}/move/{move_name.lower().replace(' ', '-')}")
        if response.status_code == 404:
            raise HTTPException(404, f"Move '{move_name}' not found")
        
        move = response.json()
        
        # Get English effect text
        effect_text = "No description available"
        for entry in move.get("effect_entries", []):
            if entry["language"]["name"] == "en":
                effect_text = entry["effect"]
                break
        
        return {
            "name": move["name"].replace("-", " ").title(),
            "type": move["type"]["name"].title(),
            "power": move["power"],
            "accuracy": move["accuracy"],
            "pp": move["pp"],
            "priority": move["priority"],
            "damage_class": move["damage_class"]["name"],
            "effect": effect_text,
            "effect_chance": move["effect_chance"],
            "generation": move["generation"]["name"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching move {move_name}: {e}")
        raise HTTPException(500, "Failed to retrieve move data")


@app.get("/")
async def root():
    """API overview and available endpoints."""
    return {
        "name": "Pokemon Knowledge API",
        "description": "Simplified Pokemon data access for LLMs",
        "endpoints": {
            "/get_pokemon_info/{name_or_id}": "Get complete Pokemon information",
            "/compare_pokemon_stats/{pokemon1}/{pokemon2}": "Compare two Pokemon's battle stats",
            "/get_type_effectiveness/{type}": "Get type matchup information",
            "/search_pokemon_by_type/{type}": "Find Pokemon of a specific type",
            "/get_move_details/{move}": "Get detailed move information"
        },
        "example_queries": [
            "/get_pokemon_info/pikachu",
            "/compare_pokemon_stats/charizard/blastoise", 
            "/get_type_effectiveness/fire",
            "/search_pokemon_by_type/dragon",
            "/get_move_details/thunderbolt"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
