from typing import Optional
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import httpx
from pydantic import BaseModel

# Create the main FastAPI app
app = FastAPI(title="MTG Card Search MCP Server", version="1.0.0")

# Create the MCP wrapper FIRST
mcp = FastApiMCP(app)

class CardSearchInput(BaseModel):
    name: str

class CardSearchOutput(BaseModel):
    name: str
    type_line: str
    oracle_text: str
    image_url: str

@mcp.tool(name="search-card", description="Search for a Magic: The Gathering card by name using the Scryfall API")
async def search_card_tool(name: str) -> str:
    """Search for a Magic: The Gathering card by name using the Scryfall API.
    
    Args:
        name: The name of the Magic: The Gathering card to search for
        
    Returns:
        A formatted string with card details including name, type, oracle text, and image URL
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.scryfall.com/cards/named",
                params={"fuzzy": name}
            )
            if response.status_code == 404:
                return f"No card found with name: {name}"
            
            data = response.json()
            card_info = f"""**{data['name']}**

**Type:** {data['type_line']}

**Oracle Text:** {data.get('oracle_text', 'No oracle text available')}

**Image URL:** {data['image_uris']['normal']}"""
            
            return card_info
        except Exception as e:
            return f"Error searching for card '{name}': {str(e)}"

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