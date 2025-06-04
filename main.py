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

# Define the FastAPI endpoint that will automatically become an MCP tool
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

# Create the MCP wrapper that will automatically convert FastAPI endpoints to MCP tools
mcp = FastApiMCP(app)

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