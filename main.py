from typing import Optional
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import httpx
from pydantic import BaseModel

# Create the main FastAPI app
app = FastAPI(title="MTG Card Search MCP Server", version="1.0.0")

class CardSearchInput(BaseModel):
    name: str

class CardSearchOutput(BaseModel):
    name: str
    type_line: str
    oracle_text: str
    image_url: str

async def search_card(name: str) -> Optional[CardSearchOutput]:
    """Search for a Magic: The Gathering card by name using the Scryfall API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.scryfall.com/cards/named",
                params={"fuzzy": name}
            )
            if response.status_code == 404:
                return None
            
            data = response.json()
            return CardSearchOutput(
                name=data["name"],
                type_line=data["type_line"],
                oracle_text=data.get("oracle_text", ""),
                image_url=data["image_uris"]["normal"]
            )
        except Exception as e:
            print(f"Error searching for card: {e}")
            return None

# Create the MCP wrapper
mcp = FastApiMCP(app)

# Add the search-card tool
@app.post("/search-card")
async def search_card_endpoint(input_data: CardSearchInput) -> Optional[CardSearchOutput]:
    """Search for a Magic: The Gathering card by name."""
    return await search_card(input_data.name)

# Mount the MCP server to make it available at /mcp
mcp.mount()

@app.get("/")
async def root():
    return {"message": "MTG Card Search MCP Server", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 