from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import httpx
import json
import asyncio
from pydantic import BaseModel

app = FastAPI(title="MTG Card Search MCP Server", version="1.0.0")

class CardSearchInput(BaseModel):
    name: str

class CardSearchOutput(BaseModel):
    name: str
    type_line: str
    oracle_text: str
    image_url: str

class MCPRequest(BaseModel):
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class MCPResponse(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

async def search_card(name: str) -> Optional[CardSearchOutput]:
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

@app.get("/")
async def root():
    return {"message": "MTG Card Search MCP Server", "version": "1.0.0"}

@app.post("/mcp/request")
async def handle_mcp_request(request: MCPRequest):
    try:
        if request.method == "tools/list":
            return MCPResponse(
                result={
                    "tools": [
                        {
                            "name": "search-card",
                            "description": "Search for a Magic: The Gathering card by name using the Scryfall API",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the Magic: The Gathering card to search for"
                                    }
                                },
                                "required": ["name"]
                            }
                        }
                    ]
                },
                id=request.id
            )
        
        elif request.method == "tools/call":
            if not request.params:
                raise HTTPException(status_code=400, detail="Missing parameters")
            
            tool_name = request.params.get("name")
            arguments = request.params.get("arguments", {})
            
            if tool_name == "search-card":
                card_name = arguments.get("name")
                if not card_name:
                    raise HTTPException(status_code=400, detail="Missing card name")
                
                result = await search_card(card_name)
                if result:
                    return MCPResponse(
                        result={
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"**{result.name}**\n\n**Type:** {result.type_line}\n\n**Oracle Text:** {result.oracle_text}\n\n**Image:** {result.image_url}"
                                }
                            ]
                        },
                        id=request.id
                    )
                else:
                    return MCPResponse(
                        result={
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"No card found with name: {card_name}"
                                }
                            ]
                        },
                        id=request.id
                    )
            else:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {request.method}")
    
    except Exception as e:
        return MCPResponse(
            error={
                "code": -1,
                "message": str(e)
            },
            id=request.id
        )

@app.get("/mcp/sse")
async def sse_endpoint():
    async def event_stream():
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': str(asyncio.get_event_loop().time())})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 