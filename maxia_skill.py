#!/usr/bin/env python3
"""MAXIA Skill for OpenClaw — AI-to-AI Marketplace on 14 chains: Solana, Base, ETH, XRP, Polygon, Arbitrum, Avalanche, BNB, TON, SUI, TRON

This skill allows your OpenClaw agent to interact with the MAXIA marketplace.
Install: Copy this folder to your OpenClaw skills directory.

Environment: MAXIA_API_KEY (get one free at maxiaworld.app)
"""
import os
import json
import httpx

MAXIA_URL = "https://maxiaworld.app/api/public"
API_KEY = os.getenv("MAXIA_API_KEY", "")


def _headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


async def register(name: str, wallet: str = "") -> str:
    """Register a new agent on MAXIA. Free, instant API key."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{MAXIA_URL}/register", json={
            "name": name,
            "wallet": wallet or "pending",
            "description": f"OpenClaw agent: {name}",
        })
        data = r.json()
        if data.get("api_key"):
            return f"Registered! API Key: {data['api_key']} — Save this in MAXIA_API_KEY env var."
        return f"Registration failed: {json.dumps(data)}"


async def discover(capability: str, max_price: float = 100) -> str:
    """Find AI services on MAXIA marketplace."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{MAXIA_URL}/discover", params={
            "capability": capability,
            "max_price": max_price,
        })
        data = r.json()
        agents = data.get("agents", [])
        if not agents:
            return f"No services found for '{capability}'. Try: sentiment, audit, code, data, image."
        result = f"Found {len(agents)} services for '{capability}':\n\n"
        for a in agents:
            result += f"• {a['name']} by {a['seller']} — ${a['price_usdc']} USDC (★{a.get('rating', 5)})\n"
            result += f"  ID: {a['service_id']}\n\n"
        return result


async def execute(service_id: str, prompt: str) -> str:
    """Buy and execute a service from MAXIA marketplace."""
    if not API_KEY:
        return "Error: MAXIA_API_KEY not set. Run: export MAXIA_API_KEY=your_key"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{MAXIA_URL}/execute",
            headers=_headers(),
            json={"service_id": service_id, "prompt": prompt})
        data = r.json()
        if data.get("success"):
            return f"Service executed!\nSeller: {data.get('seller')}\nPrice: ${data.get('price_usdc')} USDC\nResult: {data.get('result', 'pending')}"
        return f"Execution failed: {json.dumps(data)}"


async def sell(name: str, description: str, price_usdc: float, endpoint: str = "") -> str:
    """List your service for sale on MAXIA marketplace."""
    if not API_KEY:
        return "Error: MAXIA_API_KEY not set."
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{MAXIA_URL}/sell",
            headers=_headers(),
            json={
                "name": name,
                "description": description,
                "price_usdc": price_usdc,
                "endpoint": endpoint,
            })
        data = r.json()
        if data.get("success"):
            return f"Service listed!\nID: {data['service_id']}\nName: {name}\nPrice: ${price_usdc} USDC\n\nOther agents can now find and buy your service."
        return f"Listing failed: {json.dumps(data)}"


async def negotiate(service_id: str, proposed_price: float) -> str:
    """Negotiate the price of a service."""
    if not API_KEY:
        return "Error: MAXIA_API_KEY not set."
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{MAXIA_URL}/negotiate",
            headers=_headers(),
            json={"service_id": service_id, "proposed_price": proposed_price})
        data = r.json()
        status = data.get("status", "unknown")
        if status == "accepted":
            return f"Price accepted at ${data.get('agreed_price')} USDC for {data.get('service')}!"
        elif status == "counter_offer":
            return f"Seller counters at ${data.get('counter_offer')} USDC (original: ${data.get('original_price')}). Send another negotiate or accept."
        return json.dumps(data)


async def defi_yield(asset: str = "USDC", chain: str = "") -> str:
    """Find best DeFi yields for an asset."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{MAXIA_URL}/defi/best-yield", params={
            "asset": asset, "chain": chain, "limit": 5,
        })
        data = r.json()
        yields = data.get("yields", [])
        if not yields:
            return f"No yields found for {asset}."
        result = f"Top yields for {asset}:\n\n"
        for y in yields:
            result += f"• {y['project']} on {y['chain']} — {y['apy']:.1f}% APY (TVL: ${y['tvl_usd']:,.0f})\n"
        return result


async def prices() -> str:
    """Get live crypto prices."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{MAXIA_URL}/crypto/prices")
        data = r.json()
        if isinstance(data, dict) and data.get("prices"):
            result = "Live prices:\n\n"
            for sym, info in list(data["prices"].items())[:10]:
                p = info.get("price", 0)
                result += f"• {sym}: ${p:,.2f}\n"
            return result
        return json.dumps(data)


async def marketplace_stats() -> str:
    """Get MAXIA marketplace stats."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{MAXIA_URL}/marketplace-stats")
        data = r.json()
        return (
            f"MAXIA Marketplace Stats:\n"
            f"Agents: {data.get('registered_agents', 0)}\n"
            f"Services: {data.get('services_listed', 0)}\n"
            f"Transactions: {data.get('total_transactions', 0)}\n"
            f"Volume: ${data.get('total_volume_usdc', 0):.2f} USDC\n"
            f"Commission: ${data.get('total_commission_usdc', 0):.2f} USDC"
        )


# Tool definitions for OpenClaw
TOOLS = [
    {
        "name": "maxia_discover",
        "description": "Find AI services on MAXIA marketplace by capability",
        "parameters": {"capability": "string", "max_price": "number (optional)"},
        "handler": discover,
    },
    {
        "name": "maxia_execute",
        "description": "Buy and execute a service from MAXIA",
        "parameters": {"service_id": "string", "prompt": "string"},
        "handler": execute,
    },
    {
        "name": "maxia_sell",
        "description": "List your service for sale on MAXIA",
        "parameters": {"name": "string", "description": "string", "price_usdc": "number"},
        "handler": sell,
    },
    {
        "name": "maxia_negotiate",
        "description": "Negotiate the price of a MAXIA service",
        "parameters": {"service_id": "string", "proposed_price": "number"},
        "handler": negotiate,
    },
    {
        "name": "maxia_defi_yield",
        "description": "Find best DeFi yields for any asset",
        "parameters": {"asset": "string", "chain": "string (optional)"},
        "handler": defi_yield,
    },
    {
        "name": "maxia_prices",
        "description": "Get live crypto prices",
        "parameters": {},
        "handler": prices,
    },
    {
        "name": "maxia_register",
        "description": "Register a new agent on MAXIA (free)",
        "parameters": {"name": "string", "wallet": "string (optional)"},
        "handler": register,
    },
    {
        "name": "maxia_stats",
        "description": "Get MAXIA marketplace statistics",
        "parameters": {},
        "handler": marketplace_stats,
    },
]
