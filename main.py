from typing import Optional
from fastapi import FastAPI
from fastapi_mcp import Tool, MCPServer
import httpx
from pydantic import BaseModel

app = FastAPI()

class CardSearchInput(BaseModel):
    name: str

class CardSearchOutput(BaseModel):
    name: str
    type_line: str
    oracle_text: str
    image_url: str

async def search_card(name: str) -> Optional[CardSearchOutput]:
    async with httpx.AsyncClient() as client:
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
            oracle_text=data["oracle_text"],
            image_url=data["image_uris"]["normal"]
        )

search_card_tool = Tool(
    name="search-card",
    description="Search for a Magic: The Gathering card by name using the Scryfall API",
    input_schema=CardSearchInput,
    output_schema=CardSearchOutput,
    handler=search_card
)

mcp_server = MCPServer(tools=[search_card_tool])
app.include_router(mcp_server.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 