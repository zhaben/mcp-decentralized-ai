from typing import Any, List, Dict
import json
from datetime import datetime, timedelta
import random
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn

# Initialize FastMCP server
mcp = FastMCP("used-goods-marketplace")

# Sample marketplace data
MARKETPLACE_ITEMS = [
    {
        "id": "1",
        "title": "iPhone 12 Pro - Unlocked",
        "description": "Used iPhone 12 Pro, 128GB, Space Gray. Minor scratches on back, screen protector applied. Battery health 87%.",
        "category": "Electronics",
        "condition": "Good",
        "seller": "TechSeller123",
        "seller_rating": 4.8,
        "location": "San Francisco, CA",
        "posted_date": "2024-01-15",
        "images": ["iphone1.jpg", "iphone2.jpg"],
        "offers": [
            {"buyer": "BuyerJoe", "amount": 450, "message": "Quick cash sale, can pick up today", "date": "2024-01-16"},
            {"buyer": "PhoneLover", "amount": 480, "message": "Great condition! Can we meet halfway?", "date": "2024-01-17"},
            {"buyer": "TechCollector", "amount": 500, "message": "Top offer, PayPal ready", "date": "2024-01-18"}
        ],
        "asking_price": 520,
        "status": "active"
    },
    {
        "id": "2", 
        "title": "Vintage Leather Sofa - Brown",
        "description": "Beautiful vintage leather sofa from the 1970s. Some wear on arms but very comfortable. Perfect for a den or office.",
        "category": "Furniture",
        "condition": "Fair",
        "seller": "VintageHome",
        "seller_rating": 4.9,
        "location": "Portland, OR",
        "posted_date": "2024-01-10",
        "images": ["sofa1.jpg", "sofa2.jpg", "sofa3.jpg"],
        "offers": [
            {"buyer": "HomeDesigner", "amount": 300, "message": "Love the vintage look, can arrange pickup", "date": "2024-01-12"},
            {"buyer": "FurnitureFan", "amount": 275, "message": "Cash offer, flexible on pickup time", "date": "2024-01-14"}
        ],
        "asking_price": 350,
        "status": "active"
    },
    {
        "id": "3",
        "title": "Mountain Bike - Trek 2019",
        "description": "Trek mountain bike, 2019 model. Well maintained, new tires last year. Great for trails and city riding.",
        "category": "Sports",
        "condition": "Excellent",
        "seller": "BikeRider99",
        "seller_rating": 4.7,
        "location": "Denver, CO",
        "posted_date": "2024-01-20",
        "images": ["bike1.jpg", "bike2.jpg"],
        "offers": [
            {"buyer": "MountainExplorer", "amount": 800, "message": "Exactly what I'm looking for!", "date": "2024-01-21"},
            {"buyer": "CyclingEnthusiast", "amount": 750, "message": "Great bike, can we negotiate?", "date": "2024-01-22"},
            {"buyer": "TrailRider", "amount": 825, "message": "Higher offer, very interested", "date": "2024-01-23"}
        ],
        "asking_price": 850,
        "status": "active"
    },
    {
        "id": "4",
        "title": "Nintendo Switch with Games",
        "description": "Nintendo Switch console with 5 games: Mario Kart, Zelda, Animal Crossing, Mario Odyssey, and Splatoon 2. All in great condition.",
        "category": "Electronics",
        "condition": "Excellent",
        "seller": "GamerzParadise",
        "seller_rating": 4.6,
        "location": "Austin, TX",
        "posted_date": "2024-01-18",
        "images": ["switch1.jpg", "switch2.jpg"],
        "offers": [
            {"buyer": "GamerKid", "amount": 280, "message": "My dream setup! Please consider", "date": "2024-01-19"},
            {"buyer": "NintendoFan", "amount": 320, "message": "Fair offer for everything included", "date": "2024-01-20"}
        ],
        "asking_price": 350,
        "status": "active"
    },
    {
        "id": "5",
        "title": "Antique Oak Dining Table",
        "description": "Beautiful oak dining table from early 1900s. Seats 6 comfortably. Some minor scratches but very sturdy.",
        "category": "Furniture", 
        "condition": "Good",
        "seller": "AntiqueDealer",
        "seller_rating": 4.9,
        "location": "Boston, MA",
        "posted_date": "2024-01-12",
        "images": ["table1.jpg", "table2.jpg"],
        "offers": [
            {"buyer": "RestaurantOwner", "amount": 450, "message": "Perfect for my cafe, can pick up this weekend", "date": "2024-01-14"},
            {"buyer": "HomeRestorer", "amount": 400, "message": "Love antique furniture, great piece", "date": "2024-01-15"}
        ],
        "asking_price": 500,
        "status": "active"
    }
]

@mcp.tool()
async def search_items(query: str = "", category: str = "", max_price: int = 0) -> str:
    """Search for items in the marketplace.
    
    Args:
        query: Search term for item title/description
        category: Filter by category (Electronics, Furniture, Sports, etc.)
        max_price: Maximum asking price filter
    """
    try:
        filtered_items = MARKETPLACE_ITEMS.copy()
        
        # Filter by search query
        if query:
            filtered_items = [
                item for item in filtered_items
                if query.lower() in item["title"].lower() or query.lower() in item["description"].lower()
            ]
        
        # Filter by category
        if category:
            filtered_items = [
                item for item in filtered_items
                if item["category"].lower() == category.lower()
            ]
        
        # Filter by max price
        if max_price > 0:
            filtered_items = [
                item for item in filtered_items
                if item["asking_price"] <= max_price
            ]
        
        if not filtered_items:
            return "No items found matching your criteria."
        
        # Format results
        results = []
        for item in filtered_items:
            highest_offer = max(item["offers"], key=lambda x: x["amount"]) if item["offers"] else None
            highest_offer_text = f"Highest offer: ${highest_offer['amount']}" if highest_offer else "No offers yet"
            
            results.append(f"""
📦 {item['title']} (ID: {item['id']})
💰 Asking: ${item['asking_price']} | {highest_offer_text}
📍 {item['location']} | Condition: {item['condition']}
👤 Seller: {item['seller']} (⭐ {item['seller_rating']})
📝 {item['description'][:100]}{'...' if len(item['description']) > 100 else ''}
""")
        
        return f"Found {len(filtered_items)} items:\n" + "\n".join(results)
        
    except Exception as e:
        return f"Error searching items: {str(e)}"

@mcp.tool()
async def get_item_details(item_id: str) -> str:
    """Get detailed information about a specific item including all offers.
    
    Args:
        item_id: The ID of the item to retrieve
    """
    try:
        item = next((item for item in MARKETPLACE_ITEMS if item["id"] == item_id), None)
        
        if not item:
            return f"Item with ID '{item_id}' not found."
        
        # Format offers
        offers_text = ""
        if item["offers"]:
            sorted_offers = sorted(item["offers"], key=lambda x: x["amount"], reverse=True)
            offers_text = "\n💰 Current Offers:\n"
            for i, offer in enumerate(sorted_offers):
                offers_text += f"  {i+1}. ${offer['amount']} from {offer['buyer']} ({offer['date']})\n"
                offers_text += f"     Message: \"{offer['message']}\"\n"
        else:
            offers_text = "\n💰 No offers yet - be the first!"
        
        return f"""
📦 {item['title']} (ID: {item['id']})
💰 Asking Price: ${item['asking_price']}
📂 Category: {item['category']} | Condition: {item['condition']}
📍 Location: {item['location']}
👤 Seller: {item['seller']} (⭐ {item['seller_rating']}/5.0)
📅 Posted: {item['posted_date']}
🖼️ Images: {', '.join(item['images'])}

📝 Description:
{item['description']}
{offers_text}
🏷️ Status: {item['status'].upper()}
"""
        
    except Exception as e:
        return f"Error retrieving item details: {str(e)}"

@mcp.tool()
async def get_offers_for_item(item_id: str) -> str:
    """Get all offers for a specific item, sorted by amount.
    
    Args:
        item_id: The ID of the item
    """
    try:
        item = next((item for item in MARKETPLACE_ITEMS if item["id"] == item_id), None)
        
        if not item:
            return f"Item with ID '{item_id}' not found."
        
        if not item["offers"]:
            return f"No offers yet for '{item['title']}'. Asking price: ${item['asking_price']}"
        
        sorted_offers = sorted(item["offers"], key=lambda x: x["amount"], reverse=True)
        
        result = f"📦 Offers for: {item['title']} (Asking: ${item['asking_price']})\n\n"
        
        for i, offer in enumerate(sorted_offers):
            result += f"{i+1}. 💰 ${offer['amount']} from {offer['buyer']}\n"
            result += f"   📅 {offer['date']}\n"
            result += f"   💬 \"{offer['message']}\"\n\n"
        
        highest_offer = sorted_offers[0]
        percentage = (highest_offer["amount"] / item["asking_price"]) * 100
        result += f"🏆 Highest offer is {percentage:.1f}% of asking price"
        
        return result
        
    except Exception as e:
        return f"Error retrieving offers: {str(e)}"

@mcp.tool()
async def list_categories() -> str:
    """Get all available categories in the marketplace."""
    try:
        categories = list(set(item["category"] for item in MARKETPLACE_ITEMS))
        categories.sort()
        
        category_counts = {}
        for category in categories:
            count = len([item for item in MARKETPLACE_ITEMS if item["category"] == category])
            category_counts[category] = count
        
        result = "📂 Available Categories:\n\n"
        for category in categories:
            result += f"• {category} ({category_counts[category]} items)\n"
        
        return result
        
    except Exception as e:
        return f"Error listing categories: {str(e)}"

@mcp.tool()
async def get_marketplace_stats() -> str:
    """Get overall marketplace statistics."""
    try:
        total_items = len(MARKETPLACE_ITEMS)
        total_offers = sum(len(item["offers"]) for item in MARKETPLACE_ITEMS)
        
        # Calculate average asking price
        avg_asking = sum(item["asking_price"] for item in MARKETPLACE_ITEMS) / total_items
        
        # Calculate average offer amount
        all_offers = [offer["amount"] for item in MARKETPLACE_ITEMS for offer in item["offers"]]
        avg_offer = sum(all_offers) / len(all_offers) if all_offers else 0
        
        # Get category breakdown
        categories = {}
        for item in MARKETPLACE_ITEMS:
            cat = item["category"]
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        result = f"""
📊 Marketplace Statistics

📦 Total Items: {total_items}
💰 Total Offers: {total_offers}
💵 Average Asking Price: ${avg_asking:.2f}
💸 Average Offer Amount: ${avg_offer:.2f}

📂 Category Breakdown:
"""
        
        for cat, count in sorted(categories.items()):
            result += f"• {cat}: {count} items\n"
        
        return result
        
    except Exception as e:
        return f"Error generating stats: {str(e)}"

# HTML for the homepage
async def homepage(request: Request) -> HTMLResponse:
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Used Goods Marketplace - MCP Server</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid #e0e0e0;
                padding-bottom: 20px;
            }
            .marketplace-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            h1 {
                color: #2c3e50;
                margin: 10px 0;
            }
            .subtitle {
                color: #7f8c8d;
                font-size: 18px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .stat-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #3498db;
            }
            .stat-number {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
            .stat-label {
                color: #7f8c8d;
                margin-top: 5px;
            }
            .tools {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            .tool {
                margin: 15px 0;
                padding: 15px;
                background: white;
                border-left: 4px solid #e74c3c;
                border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .tool-name {
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 5px;
            }
            .tool-desc {
                color: #7f8c8d;
                font-size: 14px;
            }
            button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                margin: 10px 5px;
                cursor: pointer;
                border-radius: 6px;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            button:hover {
                background-color: #2980b9;
            }
            .connection-status {
                border: 1px solid #bdc3c7;
                padding: 15px;
                margin-top: 20px;
                border-radius: 6px;
                background: white;
                min-height: 50px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="marketplace-icon">🛒</div>
                <h1>Used Goods Marketplace</h1>
                <div class="subtitle">MCP Server for Second-Hand Items</div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">5</div>
                    <div class="stat-label">Active Listings</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">12</div>
                    <div class="stat-label">Total Offers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">4</div>
                    <div class="stat-label">Categories</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">$513</div>
                    <div class="stat-label">Avg. Asking Price</div>
                </div>
            </div>
            
            <div class="tools">
                <h3>🔧 Available Tools:</h3>
                <div class="tool">
                    <div class="tool-name">search_items</div>
                    <div class="tool-desc">Search for items by keyword, category, or price range</div>
                </div>
                <div class="tool">
                    <div class="tool-name">get_item_details</div>
                    <div class="tool-desc">Get detailed information about a specific item including all offers</div>
                </div>
                <div class="tool">
                    <div class="tool-name">get_offers_for_item</div>
                    <div class="tool-desc">View all offers for a specific item, sorted by amount</div>
                </div>
                <div class="tool">
                    <div class="tool-name">list_categories</div>
                    <div class="tool-desc">Get all available product categories</div>
                </div>
                <div class="tool">
                    <div class="tool-name">get_marketplace_stats</div>
                    <div class="tool-desc">View overall marketplace statistics and trends</div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button id="connect-button">🔗 Connect to SSE</button>
                <button id="test-button">🧪 Test Connection</button>
            </div>
            
            <div class="connection-status" id="status">
                Click "Connect to SSE" to establish MCP connection...
            </div>
        </div>
        
        <script>
            let eventSource = null;
            
            document.getElementById('connect-button').addEventListener('click', function() {
                const statusDiv = document.getElementById('status');
                
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                    statusDiv.innerHTML = '❌ Disconnected from MCP server';
                    this.textContent = '🔗 Connect to SSE';
                    return;
                }
                
                try {
                    eventSource = new EventSource('/sse');
                    statusDiv.innerHTML = '⏳ Connecting to MCP server...';
                    this.textContent = '❌ Disconnect';
                    
                    eventSource.onopen = function() {
                        statusDiv.innerHTML = '<span style="color: #27ae60;">✅ Connected to MCP server - Ready for marketplace queries!</span>';
                    };
                    
                    eventSource.onerror = function() {
                        statusDiv.innerHTML = '<span style="color: #e74c3c;">❌ Connection error - Please try again</span>';
                        eventSource.close();
                        eventSource = null;
                        document.getElementById('connect-button').textContent = '🔗 Connect to SSE';
                    };
                    
                    eventSource.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        statusDiv.innerHTML = '<span style="color: #3498db;">📡 MCP Message: ' + JSON.stringify(data) + '</span>';
                    };
                    
                } catch (e) {
                    statusDiv.innerHTML = '<span style="color: #e74c3c;">❌ Error: ' + e.message + '</span>';
                }
            });
            
            document.getElementById('test-button').addEventListener('click', function() {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<span style="color: #f39c12;">🧪 Testing MCP endpoint...</span>';
                
                fetch('/sse', { method: 'HEAD' })
                    .then(response => {
                        if (response.ok || response.status === 405) {
                            statusDiv.innerHTML = '<span style="color: #27ae60;">✅ MCP endpoint is accessible and ready</span>';
                        } else {
                            statusDiv.innerHTML = '<span style="color: #e74c3c;">❌ MCP endpoint error: ' + response.status + '</span>';
                        }
                    })
                    .catch(error => {
                        statusDiv.innerHTML = '<span style="color: #e74c3c;">❌ Connection test failed: ' + error.message + '</span>';
                    });
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html_content)

# Create Starlette application with SSE transport
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/", endpoint=homepage),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

if __name__ == "__main__":
    # Get the MCP server from FastMCP
    mcp_server = mcp._mcp_server
    
    # Create and run Starlette app
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    print("🛒 Starting Used Goods Marketplace MCP Server...")
    print("📍 Homepage: http://localhost:8080")
    print("🔗 SSE Endpoint: http://localhost:8080/sse")
    print("📡 Messages: http://localhost:8080/messages/")
    print("\n🏪 Available marketplace tools:")
    print("  • search_items - Search by keyword, category, or price")
    print("  • get_item_details - Get full item details with offers")
    print("  • get_offers_for_item - View all offers for an item")
    print("  • list_categories - Show all categories")
    print("  • get_marketplace_stats - Marketplace overview")
    
    uvicorn.run(starlette_app, host="0.0.0.0", port=8080)