from typing import Optional, List
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import httpx
import asyncio
from pydantic import BaseModel

# Create the main FastAPI app
app = FastAPI(title="MTG Card Search MCP Server", version="2.0.0")

# Input/Output models for existing search-card tool
class CardSearchInput(BaseModel):
    name: str

class CardSearchOutput(BaseModel):
    name: str
    type_line: str
    oracle_text: str
    image_url: str

# Input/Output models for new search-cards tool
class CardsSearchInput(BaseModel):
    query: str
    unique: Optional[str] = "cards"
    order: Optional[str] = "name"
    page: Optional[int] = 1

class CardResult(BaseModel):
    name: str
    type_line: str
    oracle_text: Optional[str]
    mana_cost: Optional[str]
    cmc: Optional[float]
    image_url: Optional[str]
    scryfall_id: str

class CardsSearchOutput(BaseModel):
    cards: List[CardResult]
    total_cards: int
    has_more: bool

# Input/Output models for rulings tool
class CardRulingsInput(BaseModel):
    scryfall_id: str

class Ruling(BaseModel):
    source: str
    published_at: str
    comment: str

class CardRulingsOutput(BaseModel):
    card_name: str
    scryfall_id: str
    rulings: List[Ruling]

# Input/Output models for sets tool
class SetInfo(BaseModel):
    code: str
    name: str
    set_type: str
    released_at: Optional[str]
    card_count: int
    scryfall_id: str

class SetsOutput(BaseModel):
    sets: List[SetInfo]
    total_sets: int

# NEW: Input/Output models for card symbols tool
class CardSymbol(BaseModel):
    symbol: str
    loose_variant: Optional[str]
    english: str
    transposable: bool
    represents_mana: bool
    appears_in_mana_costs: bool
    mana_value: Optional[float]
    colors: List[str]

class CardSymbolsOutput(BaseModel):
    symbols: List[CardSymbol]
    total_symbols: int

# NEW: Input/Output models for random card tool
class RandomCardOutput(BaseModel):
    name: str
    type_line: str
    oracle_text: Optional[str]
    mana_cost: Optional[str]
    cmc: Optional[float]
    image_url: Optional[str]
    scryfall_id: str
    set_name: str
    set_code: str

# NEW: Input/Output models for single set tool
class SingleSetInput(BaseModel):
    set_code: str

class SingleSetOutput(BaseModel):
    code: str
    name: str
    set_type: str
    released_at: Optional[str]
    card_count: int
    scryfall_id: str
    block: Optional[str]
    parent_set_code: Optional[str]
    digital: bool
    foil_only: bool
    icon_svg_uri: Optional[str]

# NEW: Input/Output models for catalogs tool
class CatalogInput(BaseModel):
    catalog_type: str  # "card-names", "artist-names", "word-bank", etc.

class CatalogOutput(BaseModel):
    catalog_type: str
    data: List[str]
    total_items: int

# NEW: Input/Output models for exact card name tool
class ExactCardInput(BaseModel):
    exact_name: str
    set_code: Optional[str] = None

class ExactCardOutput(BaseModel):
    name: str
    type_line: str
    oracle_text: Optional[str]
    mana_cost: Optional[str]
    cmc: Optional[float]
    image_url: Optional[str]
    scryfall_id: str
    set_name: str
    set_code: str
    rarity: str

# Rate limiting helper
async def rate_limit():
    """Add delay between API calls as recommended by Scryfall (50-100ms)"""
    await asyncio.sleep(0.075)  # 75ms delay

# EXISTING TOOL - Keep stable
@app.post("/search-card", operation_id="search_card")
async def search_card(input_data: CardSearchInput) -> CardSearchOutput:
    """Search for a Magic: The Gathering card by name using the Scryfall API.
    
    This endpoint searches for MTG cards and returns detailed information including
    the card's name, type line, oracle text, and image URL.
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            response = await client.get(
                f"https://api.scryfall.com/cards/named",
                params={"fuzzy": input_data.name}
            )
            if response.status_code == 404:
                # Return a placeholder response for cards not found
                return CardSearchOutput(
                    name=f"Card not found: {input_data.name}",
                    type_line="Not Found",
                    oracle_text=f"No Magic: The Gathering card found with the name '{input_data.name}'",
                    image_url=""
                )
            
            data = response.json()
            return CardSearchOutput(
                name=data["name"],
                type_line=data["type_line"],
                oracle_text=data.get("oracle_text", "No oracle text available"),
                image_url=data.get("image_uris", {}).get("normal", "")
            )
        except Exception as e:
            # Return error information as a valid response
            return CardSearchOutput(
                name=f"Error searching for: {input_data.name}",
                type_line="Error",
                oracle_text=f"An error occurred while searching: {str(e)}",
                image_url=""
            )

# EXISTING TOOL - Advanced card search with filters
@app.post("/search-cards", operation_id="search_cards")
async def search_cards(input_data: CardsSearchInput) -> CardsSearchOutput:
    """Search for Magic: The Gathering cards using advanced query syntax.
    
    This endpoint uses Scryfall's fulltext search system. You can search by:
    - Card names (e.g., "Lightning Bolt")
    - Types (e.g., "t:creature")
    - Colors (e.g., "c:red")
    - Mana cost (e.g., "cmc:3")
    - Set codes (e.g., "s:khm")
    - And many more advanced filters
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            params = {
                "q": input_data.query,
                "unique": input_data.unique,
                "order": input_data.order,
                "page": input_data.page
            }
            
            response = await client.get("https://api.scryfall.com/cards/search", params=params)
            
            if response.status_code == 404:
                return CardsSearchOutput(cards=[], total_cards=0, has_more=False)
            
            response.raise_for_status()
            data = response.json()
            
            cards = []
            for card_data in data.get("data", []):
                cards.append(CardResult(
                    name=card_data["name"],
                    type_line=card_data["type_line"],
                    oracle_text=card_data.get("oracle_text"),
                    mana_cost=card_data.get("mana_cost"),
                    cmc=card_data.get("cmc"),
                    image_url=card_data.get("image_uris", {}).get("normal"),
                    scryfall_id=card_data["id"]
                ))
            
            return CardsSearchOutput(
                cards=cards,
                total_cards=data.get("total_cards", len(cards)),
                has_more=data.get("has_more", False)
            )
            
        except Exception as e:
            return CardsSearchOutput(
                cards=[],
                total_cards=0,
                has_more=False
            )

# EXISTING TOOL - Get card rulings
@app.post("/card-rulings", operation_id="get_card_rulings")
async def get_card_rulings(input_data: CardRulingsInput) -> CardRulingsOutput:
    """Get official rulings for a Magic: The Gathering card by its Scryfall ID.
    
    This endpoint returns all official rulings and clarifications for a specific card.
    You need the Scryfall ID of the card, which you can get from the search tools.
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            # First get the card name
            card_response = await client.get(f"https://api.scryfall.com/cards/{input_data.scryfall_id}")
            card_name = "Unknown Card"
            
            if card_response.status_code == 200:
                card_data = card_response.json()
                card_name = card_data.get("name", "Unknown Card")
            
            await rate_limit()
            # Get the rulings
            rulings_response = await client.get(f"https://api.scryfall.com/cards/{input_data.scryfall_id}/rulings")
            
            if rulings_response.status_code == 404:
                return CardRulingsOutput(
                    card_name=card_name,
                    scryfall_id=input_data.scryfall_id,
                    rulings=[]
                )
            
            rulings_response.raise_for_status()
            rulings_data = rulings_response.json()
            
            rulings = []
            for ruling_data in rulings_data.get("data", []):
                rulings.append(Ruling(
                    source=ruling_data.get("source", ""),
                    published_at=ruling_data.get("published_at", ""),
                    comment=ruling_data.get("comment", "")
                ))
            
            return CardRulingsOutput(
                card_name=card_name,
                scryfall_id=input_data.scryfall_id,
                rulings=rulings
            )
            
        except Exception as e:
            return CardRulingsOutput(
                card_name="Error",
                scryfall_id=input_data.scryfall_id,
                rulings=[Ruling(
                    source="error",
                    published_at="",
                    comment=f"Error retrieving rulings: {str(e)}"
                )]
            )

# EXISTING TOOL - Get all MTG sets
@app.get("/sets", operation_id="get_all_sets")
async def get_all_sets() -> SetsOutput:
    """Get a list of all Magic: The Gathering sets available on Scryfall.
    
    This endpoint returns information about all MTG sets including their codes,
    names, types, release dates, and card counts.
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            response = await client.get("https://api.scryfall.com/sets")
            response.raise_for_status()
            data = response.json()
            
            sets = []
            for set_data in data.get("data", []):
                sets.append(SetInfo(
                    code=set_data.get("code", ""),
                    name=set_data.get("name", ""),
                    set_type=set_data.get("set_type", ""),
                    released_at=set_data.get("released_at"),
                    card_count=set_data.get("card_count", 0),
                    scryfall_id=set_data.get("id", "")
                ))
            
            return SetsOutput(
                sets=sets,
                total_sets=len(sets)
            )
            
        except Exception as e:
            return SetsOutput(
                sets=[SetInfo(
                    code="error",
                    name="Error retrieving sets",
                    set_type="error",
                    released_at=None,
                    card_count=0,
                    scryfall_id=""
                )],
                total_sets=0
            )

# NEW TOOL - Get card symbols
@app.get("/card-symbols", operation_id="get_card_symbols")
async def get_card_symbols() -> CardSymbolsOutput:
    """Get all mana symbols and card symbols used in Magic: The Gathering.
    
    This endpoint returns information about mana symbols, including their meanings,
    mana values, colors, and whether they appear in mana costs.
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            response = await client.get("https://api.scryfall.com/symbology")
            response.raise_for_status()
            data = response.json()
            
            symbols = []
            for symbol_data in data.get("data", []):
                symbols.append(CardSymbol(
                    symbol=symbol_data.get("symbol", ""),
                    loose_variant=symbol_data.get("loose_variant"),
                    english=symbol_data.get("english", ""),
                    transposable=symbol_data.get("transposable", False),
                    represents_mana=symbol_data.get("represents_mana", False),
                    appears_in_mana_costs=symbol_data.get("appears_in_mana_costs", False),
                    mana_value=symbol_data.get("mana_value"),
                    colors=symbol_data.get("colors", [])
                ))
            
            return CardSymbolsOutput(
                symbols=symbols,
                total_symbols=len(symbols)
            )
            
        except Exception as e:
            return CardSymbolsOutput(
                symbols=[],
                total_symbols=0
            )

# NEW TOOL - Get random card
@app.get("/random-card", operation_id="get_random_card")
async def get_random_card() -> RandomCardOutput:
    """Get a random Magic: The Gathering card.
    
    This endpoint returns a randomly selected card from Scryfall's database.
    Great for discovery and inspiration!
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            response = await client.get("https://api.scryfall.com/cards/random")
            response.raise_for_status()
            data = response.json()
            
            return RandomCardOutput(
                name=data.get("name", ""),
                type_line=data.get("type_line", ""),
                oracle_text=data.get("oracle_text"),
                mana_cost=data.get("mana_cost"),
                cmc=data.get("cmc"),
                image_url=data.get("image_uris", {}).get("normal"),
                scryfall_id=data.get("id", ""),
                set_name=data.get("set_name", ""),
                set_code=data.get("set", "")
            )
            
        except Exception as e:
            return RandomCardOutput(
                name="Error",
                type_line="Error",
                oracle_text=f"Error getting random card: {str(e)}",
                mana_cost=None,
                cmc=None,
                image_url=None,
                scryfall_id="",
                set_name="",
                set_code=""
            )

# NEW TOOL - Get single set details
@app.post("/set-details", operation_id="get_set_details")
async def get_set_details(input_data: SingleSetInput) -> SingleSetOutput:
    """Get detailed information about a specific Magic: The Gathering set.
    
    This endpoint returns comprehensive information about a set including
    block information, digital status, and icon URIs.
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            response = await client.get(f"https://api.scryfall.com/sets/{input_data.set_code}")
            
            if response.status_code == 404:
                return SingleSetOutput(
                    code=input_data.set_code,
                    name="Set not found",
                    set_type="unknown",
                    released_at=None,
                    card_count=0,
                    scryfall_id="",
                    block=None,
                    parent_set_code=None,
                    digital=False,
                    foil_only=False,
                    icon_svg_uri=None
                )
            
            response.raise_for_status()
            data = response.json()
            
            return SingleSetOutput(
                code=data.get("code", ""),
                name=data.get("name", ""),
                set_type=data.get("set_type", ""),
                released_at=data.get("released_at"),
                card_count=data.get("card_count", 0),
                scryfall_id=data.get("id", ""),
                block=data.get("block"),
                parent_set_code=data.get("parent_set_code"),
                digital=data.get("digital", False),
                foil_only=data.get("foil_only", False),
                icon_svg_uri=data.get("icon_svg_uri")
            )
            
        except Exception as e:
            return SingleSetOutput(
                code=input_data.set_code,
                name="Error",
                set_type="error",
                released_at=None,
                card_count=0,
                scryfall_id="",
                block=None,
                parent_set_code=None,
                digital=False,
                foil_only=False,
                icon_svg_uri=None
            )

# NEW TOOL - Get catalog data
@app.post("/catalog", operation_id="get_catalog")
async def get_catalog(input_data: CatalogInput) -> CatalogOutput:
    """Get catalog data from Scryfall (card names, artist names, etc.).
    
    Available catalog types:
    - card-names: All card names
    - artist-names: All artist names  
    - word-bank: All words that appear in card names
    - creature-types: All creature types
    - planeswalker-types: All planeswalker types
    - land-types: All land types
    - artifact-types: All artifact types
    - enchantment-types: All enchantment types
    - spell-types: All spell types
    - powers: All power values
    - toughnesses: All toughness values
    - loyalties: All loyalty values
    - watermarks: All watermarks
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            response = await client.get(f"https://api.scryfall.com/catalog/{input_data.catalog_type}")
            
            if response.status_code == 404:
                return CatalogOutput(
                    catalog_type=input_data.catalog_type,
                    data=[],
                    total_items=0
                )
            
            response.raise_for_status()
            data = response.json()
            
            return CatalogOutput(
                catalog_type=input_data.catalog_type,
                data=data.get("data", []),
                total_items=len(data.get("data", []))
            )
            
        except Exception as e:
            return CatalogOutput(
                catalog_type=input_data.catalog_type,
                data=[],
                total_items=0
            )

# NEW TOOL - Get card by exact name
@app.post("/exact-card", operation_id="get_exact_card")
async def get_exact_card(input_data: ExactCardInput) -> ExactCardOutput:
    """Get a Magic: The Gathering card by its exact name.
    
    This is faster and more precise than fuzzy search when you know the exact name.
    Optionally specify a set code to get the card from a specific set.
    """
    async with httpx.AsyncClient() as client:
        try:
            await rate_limit()
            params = {"exact": input_data.exact_name}
            if input_data.set_code:
                params["set"] = input_data.set_code
                
            response = await client.get("https://api.scryfall.com/cards/named", params=params)
            
            if response.status_code == 404:
                return ExactCardOutput(
                    name=f"Card not found: {input_data.exact_name}",
                    type_line="Not Found",
                    oracle_text=f"No card found with exact name '{input_data.exact_name}'",
                    mana_cost=None,
                    cmc=None,
                    image_url=None,
                    scryfall_id="",
                    set_name="",
                    set_code="",
                    rarity=""
                )
            
            response.raise_for_status()
            data = response.json()
            
            return ExactCardOutput(
                name=data.get("name", ""),
                type_line=data.get("type_line", ""),
                oracle_text=data.get("oracle_text"),
                mana_cost=data.get("mana_cost"),
                cmc=data.get("cmc"),
                image_url=data.get("image_uris", {}).get("normal"),
                scryfall_id=data.get("id", ""),
                set_name=data.get("set_name", ""),
                set_code=data.get("set", ""),
                rarity=data.get("rarity", "")
            )
            
        except Exception as e:
            return ExactCardOutput(
                name=f"Error: {input_data.exact_name}",
                type_line="Error",
                oracle_text=f"Error retrieving card: {str(e)}",
                mana_cost=None,
                cmc=None,
                image_url=None,
                scryfall_id="",
                set_name="",
                set_code="",
                rarity=""
            )

# Create the MCP wrapper that will automatically convert FastAPI endpoints to MCP tools
mcp = FastApiMCP(app)

# Mount the MCP server to make it available at /mcp
mcp.mount()

@app.get("/")
async def root():
    return {
        "message": "MTG Card Search MCP Server", 
        "version": "2.0.0", 
        "tools": [
            "search_card", 
            "search_cards", 
            "get_card_rulings", 
            "get_all_sets",
            "get_card_symbols",
            "get_random_card",
            "get_set_details",
            "get_catalog",
            "get_exact_card"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 