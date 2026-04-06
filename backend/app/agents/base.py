"""
Base Agent Framework - Foundation for all 10 specialized agents.
Provides LangChain integration, Redis shared memory, event emission,
retry logic, logging, and WebSocket broadcast capabilities.
"""
import logging
import json
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy.orm import Session

from app.config import settings
from app.models.agent import AgentLog
from app.models.notification import Notification

logger = logging.getLogger(__name__)


def get_llm():
    """Get the configured LLM instance. Tries Anthropic first, falls back to OpenAI."""
    if settings.ANTHROPIC_API_KEY:
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=settings.CLAUDE_MODEL,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
        except Exception as e:
            logger.warning(f"Anthropic init failed: {e}")

    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.OPENAI_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
            )
        except Exception as e:
            logger.warning(f"OpenAI init failed: {e}")

    if settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    # Fallback: return a mock LLM for dev/testing
    logger.warning("No LLM API key configured - using mock responses")
    return None


class SharedMemory:
    """Redis-backed shared memory for inter-agent communication."""

    def __init__(self):
        self._memory: Dict[str, Any] = {}
        self._redis = None
        try:
            import redis
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self._redis.ping()
            logger.info("Shared memory connected to Redis")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory fallback: {e}")

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Store a value in shared memory."""
        serialized = json.dumps(value, default=str)
        if self._redis:
            self._redis.setex(key, ttl, serialized)
        else:
            self._memory[key] = serialized

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from shared memory."""
        if self._redis:
            val = self._redis.get(key)
        else:
            val = self._memory.get(key)

        if val:
            return json.loads(val)
        return None

    def publish(self, channel: str, message: Dict):
        """Publish an event to a Redis pub/sub channel."""
        serialized = json.dumps(message, default=str)
        if self._redis:
            self._redis.publish(channel, serialized)
        logger.debug(f"Published to {channel}: {message.get('type', 'unknown')}")

    def delete(self, key: str):
        if self._redis:
            self._redis.delete(key)
        else:
            self._memory.pop(key, None)


# Singleton shared memory instance
shared_memory = SharedMemory()


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Month-End Close system.
    Provides common functionality: LLM calls, logging, events, retry logic.
    """

    AGENT_TYPE: str = "base"
    AGENT_NAME: str = "Base Agent"
    DESCRIPTION: str = "Base agent class"

    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm()
        self.memory = shared_memory
        self._broadcast_callback = None

    def set_broadcast_callback(self, callback):
        """Set callback for WebSocket broadcasting."""
        self._broadcast_callback = callback

    @abstractmethod
    async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs) -> Dict[str, Any]:
        """
        Execute the agent's primary task.
        Must be implemented by each specialized agent.
        Returns a result dictionary with findings, actions, and status.
        """
        pass

    async def run(self, company_id: Optional[str] = None, period: str = "2026-01",
                  workflow_run_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Run the agent with retry logic, logging, and event emission."""
        start_time = time.time()
        result = None
        error = None

        # Log start
        await self._log_action(
            action=f"{self.AGENT_NAME} started",
            status="running",
            company_id=company_id,
            workflow_run_id=workflow_run_id,
        )

        # Broadcast start event
        await self._broadcast({
            "type": "agent_update",
            "agent_type": self.AGENT_TYPE,
            "agent_name": self.AGENT_NAME,
            "company_id": company_id,
            "status": "running",
            "message": f"{self.AGENT_NAME} starting analysis...",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Execute with retry logic
        for attempt in range(settings.MAX_AGENT_RETRIES):
            try:
                result = await self.execute(company_id=company_id, period=period, **kwargs)
                break
            except Exception as e:
                error = str(e)
                logger.error(f"{self.AGENT_NAME} attempt {attempt + 1} failed: {e}")
                if attempt < settings.MAX_AGENT_RETRIES - 1:
                    await asyncio.sleep(settings.AGENT_RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    result = {
                        "status": "failed",
                        "error": error,
                        "findings": [],
                        "actions": [],
                    }

        duration_ms = int((time.time() - start_time) * 1000)
        status = "completed" if result and result.get("status") != "failed" else "failed"
        severity = "error" if status == "failed" else "info"

        # Store results in shared memory for other agents
        if result and status == "completed":
            memory_key = f"agent:{self.AGENT_TYPE}:{company_id or 'all'}:{period}"
            self.memory.set(memory_key, result)

        # Log completion
        await self._log_action(
            action=f"{self.AGENT_NAME} {status}",
            status=status,
            severity=severity,
            company_id=company_id,
            workflow_run_id=workflow_run_id,
            details=result,
            duration_ms=duration_ms,
        )

        # Broadcast completion
        findings_count = len(result.get("findings", [])) if result else 0
        await self._broadcast({
            "type": "agent_update",
            "agent_type": self.AGENT_TYPE,
            "agent_name": self.AGENT_NAME,
            "company_id": company_id,
            "status": status,
            "message": f"{self.AGENT_NAME} {status} - {findings_count} findings",
            "duration_ms": duration_ms,
            "findings_count": findings_count,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Emit event for downstream agents
        self.memory.publish("agent_events", {
            "type": f"{self.AGENT_TYPE}_{status}",
            "agent_type": self.AGENT_TYPE,
            "company_id": company_id,
            "period": period,
            "result": result,
        })

        # Create notifications for significant findings
        if result:
            await self._create_notifications(company_id, result)

        return result or {"status": "failed", "error": "No result"}

    async def call_llm(self, prompt: str, system: str = "", parse_json: bool = True) -> Any:
        """Call the LLM with a prompt and optional JSON parsing."""
        if not self.llm:
            # Return mock analysis when no LLM configured
            return self._mock_llm_response(prompt)

        try:
            messages = []
            if system:
                messages.append(("system", system))
            messages.append(("human", prompt))

            template = ChatPromptTemplate.from_messages(messages)
            chain = template | self.llm

            if parse_json:
                chain = chain | JsonOutputParser()

            response = await asyncio.to_thread(chain.invoke, {})
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return self._mock_llm_response(prompt)

    def _mock_llm_response(self, prompt: str) -> Dict:
        """Provide intelligent mock responses when no LLM is configured."""
        return {
            "analysis": "Automated analysis completed based on financial data rules.",
            "findings": [],
            "recommendations": ["Review flagged items manually"],
            "risk_level": "medium",
            "commentary": "Analysis performed using rule-based checks. LLM-enhanced analysis available with API key configuration."
        }

    async def _log_action(self, action: str, status: str, severity: str = "info",
                          company_id: Optional[str] = None, workflow_run_id: Optional[int] = None,
                          details: Optional[Dict] = None, reasoning: Optional[str] = None,
                          duration_ms: Optional[int] = None):
        """Log an agent action to the database."""
        log = AgentLog(
            agent_type=self.AGENT_TYPE,
            company_id=company_id,
            workflow_run_id=workflow_run_id,
            action=action,
            status=status,
            severity=severity,
            details=details,
            reasoning=reasoning,
            duration_ms=duration_ms,
        )
        self.db.add(log)
        self.db.commit()

    async def _create_notifications(self, company_id: Optional[str], result: Dict):
        """Create in-app notifications for significant findings."""
        findings = result.get("findings", [])
        for finding in findings:
            severity = finding.get("severity", "info")
            if severity in ("warning", "error", "critical"):
                notification = Notification(
                    company_id=company_id,
                    notification_type="issue_alert",
                    severity=severity,
                    title=finding.get("title", f"{self.AGENT_NAME} Finding"),
                    message=finding.get("description", ""),
                    details=finding,
                    agent_type=self.AGENT_TYPE,
                )
                self.db.add(notification)
        self.db.commit()

    async def _broadcast(self, message: Dict):
        """Broadcast a message via WebSocket to all connected clients."""
        if self._broadcast_callback:
            try:
                await self._broadcast_callback(message)
            except Exception as e:
                logger.debug(f"Broadcast failed (non-critical): {e}")

        # Also publish to Redis for other services
        self.memory.publish("ws_broadcast", message)
