"""
Agent connectors: abstract interface + concrete implementations.

MockAgentConnector  – deterministic responses for testing the pipeline.
APIAgentConnector   – real HTTP calls to a running agent endpoint.
"""

from __future__ import annotations

import asyncio
import random
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AgentConnector(ABC):
    """Abstract base for connecting to an agent under test."""

    @abstractmethod
    async def send_message(self, message: str, context: Dict | None = None) -> Dict[str, Any]:
        """Send a user message and return the agent's response.

        Returns:
            {
                "success": bool,
                "response": str,          # agent text reply
                "tool_calls": [...],       # list of tool-call dicts
                "error": str | None
            }
        """

    @abstractmethod
    async def reset(self) -> None:
        """Reset conversation / session state."""


# ──────────────────────────────────────────────────────────────────
# Mock connector (for pipeline testing without a live agent)
# ──────────────────────────────────────────────────────────────────


_MOCK_RESPONSES = [
    "I'd be happy to help you with that. Let me look into it.",
    "Sure, let me check that information for you right away.",
    "I've found the details you're looking for. Here's what I have:",
    "Let me process that request. One moment please.",
    "I understand your concern. Here's what I can do for you.",
    "Great question! Based on our records, here's the information:",
    "I've completed that action for you. Is there anything else?",
    "Thank you for your patience. The request has been processed.",
]

_MOCK_TOOL_NAMES = [
    "executeToolCall",
    "createClientsRoutes",
    "createAppointmentsRoutes",
    "executeEscalateToHuman",
    "createLeadsRoutes",
    "fetchData",
]


class MockAgentConnector(AgentConnector):
    """Simulates an agent with deterministic (random-seeded) responses.

    Configurable behaviours:
    - ``fail_rate``: probability [0..1] that a response fails.
    - ``tool_call_rate``: probability a response includes mock tool calls.
    - ``latency_range``: (min_ms, max_ms) simulated network latency.
    - ``available_tools``: tool names the mock agent can "call".
    """

    def __init__(
        self,
        agent_map: Dict,
        fail_rate: float = 0.05,
        tool_call_rate: float = 0.4,
        latency_range: tuple[int, int] = (50, 300),
        available_tools: List[str] | None = None,
    ):
        self.agent_map = agent_map
        self.fail_rate = fail_rate
        self.tool_call_rate = tool_call_rate
        self.latency_range = latency_range
        self.session_id: str | None = None
        self.turn_count = 0

        self.available_tools = available_tools or [
            t["name"]
            for t in agent_map.get("components", {}).get("tools", [])
        ]
        # Dedupe
        self.available_tools = list(dict.fromkeys(self.available_tools))

    async def send_message(self, message: str, context: Dict | None = None) -> Dict[str, Any]:
        # Simulate latency
        latency_ms = random.randint(*self.latency_range)
        await asyncio.sleep(latency_ms / 1000)

        self.turn_count += 1

        # Simulate failure
        if random.random() < self.fail_rate:
            return {
                "success": False,
                "response": "",
                "tool_calls": [],
                "error": "Mock agent error: service unavailable",
            }

        # Pick a response
        response_text = random.choice(_MOCK_RESPONSES)

        # Optionally simulate tool calls
        tool_calls: List[Dict] = []
        if random.random() < self.tool_call_rate and self.available_tools:
            tool_name = random.choice(self.available_tools)
            tool_calls.append({
                "tool_name": tool_name,
                "tool_id": str(uuid.uuid4())[:8],
                "arguments": {"query": message[:50]},
                "result": {"status": "ok", "data": "mock_result"},
            })

        return {
            "success": True,
            "response": response_text,
            "tool_calls": tool_calls,
            "error": None,
        }

    async def reset(self) -> None:
        self.session_id = str(uuid.uuid4())
        self.turn_count = 0


# ──────────────────────────────────────────────────────────────────
# API connector (for real agent endpoints)
# ──────────────────────────────────────────────────────────────────


class APIAgentConnector(AgentConnector):
    """Connect to an agent via HTTP API."""

    def __init__(self, agent_map: Dict):
        self.endpoint: str = agent_map.get("api_endpoint", "")
        self.api_key: str = agent_map.get("api_key", "")
        self.session_id: str | None = None
        self.timeout_sec: int = agent_map.get("success_criteria", {}).get(
            "max_latency_ms", 30_000
        ) // 1000

    async def send_message(self, message: str, context: Dict | None = None) -> Dict[str, Any]:
        import aiohttp

        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "message": message,
            "session_id": self.session_id,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.endpoint}/chat",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_sec),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "response": data.get("response", ""),
                            "tool_calls": data.get("tool_calls", []),
                            "error": None,
                        }
                    else:
                        body = await resp.text()
                        return {
                            "success": False,
                            "response": "",
                            "tool_calls": [],
                            "error": f"HTTP {resp.status}: {body[:200]}",
                        }
        except asyncio.TimeoutError:
            return {"success": False, "response": "", "tool_calls": [], "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "response": "", "tool_calls": [], "error": str(e)}

    async def reset(self) -> None:
        self.session_id = str(uuid.uuid4())


# ──────────────────────────────────────────────────────────────────
# Victoria connector (for Victoria agent's debug conversation API)
# ──────────────────────────────────────────────────────────────────


class VictoriaConnector(AgentConnector):
    """Connect to Victoria agent via its authenticated debug conversation API.
    
    Victoria uses session cookie authentication:
    1. Create debug conversation: POST /conversations/debug
    2. Send messages: POST /conversations/:id/debug-message
    
    Requires a session cookie from Pulpoo authentication.
    You can get this by:
    - Logging into Victoria in your browser
    - Opening DevTools > Application > Cookies
    - Copy the 'session' cookie value
    - Set it in agent_map.json as "session_cookie" in metadata
    """

    def __init__(self, agent_map: Dict):
        import os
        
        # Extract endpoint from environment variable (preferred), then agent_map
        base_endpoint = (
            os.getenv("VICTORIA_API_ENDPOINT") or
            agent_map.get("api_endpoint") or 
            agent_map.get("metadata", {}).get("api_endpoint", "")
        )
        
        if not base_endpoint:
            # Try to construct from app_id or use default
            app_id = agent_map.get("metadata", {}).get("app_id", "victoria-tlahuac")
            base_endpoint = f"http://localhost:3200/api/{app_id}"
        
        self.base_endpoint = base_endpoint.rstrip("/")
        self.api_key: str = agent_map.get("api_key", "")
        
        # Get session cookie from environment variable (preferred) or agent_map
        self.session_cookie: str = (
            os.getenv("VICTORIA_SESSION_COOKIE") or
            agent_map.get("session_cookie") or 
            agent_map.get("metadata", {}).get("session_cookie", "")
        )
        
        if not self.session_cookie:
            raise ValueError(
                "VictoriaConnector requires 'VICTORIA_SESSION_COOKIE' environment variable or "
                "'session_cookie' in agent_map. "
                "Get it from your browser DevTools > Application > Cookies after logging into Victoria."
            )
        
        self.conversation_id: str | None = None
        self.timeout_sec: int = agent_map.get("success_criteria", {}).get(
            "max_latency_ms", 30_000
        ) // 1000

    async def reset(self) -> None:
        """Create a new debug conversation."""
        import aiohttp

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Cookie": f"session={self.session_cookie}",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Create debug conversation
        payload = {
            "clientPhone": f"DEBUG-{uuid.uuid4()}",
            "clientName": "Test User",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_endpoint}/conversations/debug",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_sec),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.conversation_id = data.get("conversationId") or data.get("conversation", {}).get("id")
                        if not self.conversation_id:
                            raise ValueError("Failed to get conversation ID from Victoria API")
                    elif resp.status == 401:
                        raise Exception(
                            "Authentication failed. Session cookie may be invalid or expired. "
                            "Please get a fresh session cookie from your browser."
                        )
                    else:
                        body = await resp.text()
                        raise Exception(f"Failed to create debug conversation: HTTP {resp.status}: {body[:200]}")
        except Exception as e:
            raise Exception(f"Victoria connector reset failed: {e}")

    async def send_message(self, message: str, context: Dict | None = None) -> Dict[str, Any]:
        """Send message to Victoria debug conversation."""
        import aiohttp

        if not self.conversation_id:
            await self.reset()

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Cookie": f"session={self.session_cookie}",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"message": message}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_endpoint}/conversations/{self.conversation_id}/debug-message",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_sec),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Extract response text
                        response_text = data.get("response", "") or data.get("aiResponse", "")
                        
                        # Extract tool calls from actions
                        tool_calls = []
                        actions = data.get("actions", [])
                        for action in actions:
                            if isinstance(action, dict):
                                action_type = action.get("actionType", "")
                                action_data = action.get("actionData", {})
                                if action_type and action_type != "ai_process_message":
                                    tool_calls.append({
                                        "tool_name": action_type,
                                        "tool_id": str(action.get("id", uuid.uuid4())),
                                        "arguments": action_data,
                                        "result": action.get("result"),
                                    })
                        
                        return {
                            "success": True,
                            "response": response_text,
                            "tool_calls": tool_calls,
                            "error": None,
                        }
                    elif resp.status == 401:
                        return {
                            "success": False,
                            "response": "",
                            "tool_calls": [],
                            "error": "Authentication failed. Session cookie may be invalid or expired.",
                        }
                    else:
                        body = await resp.text()
                        return {
                            "success": False,
                            "response": "",
                            "tool_calls": [],
                            "error": f"HTTP {resp.status}: {body[:200]}",
                        }
        except asyncio.TimeoutError:
            return {"success": False, "response": "", "tool_calls": [], "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "response": "", "tool_calls": [], "error": str(e)}
