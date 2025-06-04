from typing import Optional, List
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import httpx
from pydantic import BaseModel

# Create the main FastAPI app
app = FastAPI(title="MTG Card Search MCP Server", version="1.0.0")

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

# EXISTING TOOL - Keep stable
@app.post("/search-card", operation_id="search_card")
async def search_card(input_data: CardSearchInput) -> CardSearchOutput:
    """Search for a Magic: The Gathering card by name using the Scryfall API.
    
    This endpoint searches for MTG cards and returns detailed information including
    the card's name, type line, oracle text, and image URL.
    """
    async with httpx.AsyncClient() as client:
        try:
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
                image_url=data["image_uris"]["normal"]
            )
        except Exception as e:
            # Return error information as a valid response
            return CardSearchOutput(
                name=f"Error searching for: {input_data.name}",
                type_line="Error",
                oracle_text=f"An error occurred while searching: {str(e)}",
                image_url=""
            )

# NEW TOOL - Advanced card search with filters
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

# NEW TOOL - Get card rulings
@app.post("/card-rulings", operation_id="get_card_rulings")
async def get_card_rulings(input_data: CardRulingsInput) -> CardRulingsOutput:
    """Get official rulings for a Magic: The Gathering card by its Scryfall ID.
    
    This endpoint returns all official rulings and clarifications for a specific card.
    You need the Scryfall ID of the card, which you can get from the search tools.
    """
    async with httpx.AsyncClient() as client:
        try:
            # First get the card name
            card_response = await client.get(f"https://api.scryfall.com/cards/{input_data.scryfall_id}")
            card_name = "Unknown Card"
            
            if card_response.status_code == 200:
                card_data = card_response.json()
                card_name = card_data.get("name", "Unknown Card")
            
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

# NEW TOOL - Get all MTG sets
@app.get("/sets", operation_id="get_all_sets")
async def get_all_sets() -> SetsOutput:
    """Get a list of all Magic: The Gathering sets available on Scryfall.
    
    This endpoint returns information about all MTG sets including their codes,
    names, types, release dates, and card counts.
    """
    async with httpx.AsyncClient() as client:
        try:
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

# Create the MCP wrapper that will automatically convert FastAPI endpoints to MCP tools
mcp = FastApiMCP(app)

# Mount the MCP server to make it available at /mcp
mcp.mount()

@app.get("/")
async def root():
    return {"message": "MTG Card Search MCP Server", "version": "1.0.0", "tools": ["search_card", "search_cards", "get_card_rulings", "get_all_sets"]}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 