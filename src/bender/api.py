"""HTTP API endpoints — FastAPI routes for external triggers."""

import logging

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from bender.claude_code import ClaudeCodeError, invoke_claude
from bender.config import Settings
from bender.session_manager import SessionManager
from bender.slack_utils import SLACK_MSG_LIMIT, md_to_mrkdwn, split_text

logger = logging.getLogger(__name__)

security = HTTPBearer()


class InvokeRequest(BaseModel):
    """Request body for the /api/invoke endpoint."""

    channel: str
    message: str


class InvokeResponse(BaseModel):
    """Response body for the /api/invoke endpoint."""

    thread_ts: str
    session_id: str
    response: str


def create_api(
    fastapi_app: FastAPI,
    slack_client: AsyncWebClient,
    settings: Settings,
    sessions: SessionManager,
) -> None:
    """Register API routes on the FastAPI app."""

    async def verify_api_key(
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> None:
        """Verify the Bearer token matches the configured API key."""
        if not settings.bender_api_key:
            raise HTTPException(
                status_code=503,
                detail="API key not configured on the server",
            )
        if credentials.credentials != settings.bender_api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

    @fastapi_app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint."""
        return {"status": "ok"}

    @fastapi_app.post(
        "/api/invoke",
        response_model=InvokeResponse,
        dependencies=[Depends(verify_api_key)],
    )
    async def invoke(request: InvokeRequest) -> InvokeResponse:
        """Invoke Claude Code from an external trigger.

        Posts a message in the specified channel, creates a thread,
        invokes Claude Code, and posts the response in the thread.
        """
        logger.info("API invoke: channel=%s", request.channel)

        # Post the initial message to create a thread
        try:
            post_result = await slack_client.chat_postMessage(
                channel=request.channel,
                text=f"External trigger: {request.message}",
            )
        except SlackApiError as exc:
            logger.error("Failed to post to Slack: %s", exc)
            raise HTTPException(
                status_code=502, detail="Failed to post message to Slack"
            ) from exc

        thread_ts = post_result["ts"]
        session_id = await sessions.create_session(thread_ts)

        # Invoke Claude Code
        try:
            response = await invoke_claude(
                prompt=request.message,
                workspace=settings.bender_workspace,
                session_id=session_id,
            )
        except ClaudeCodeError as exc:
            logger.error("Claude Code invocation failed: %s", exc)
            await slack_client.chat_postMessage(
                channel=request.channel,
                thread_ts=thread_ts,
                text="An error occurred while processing this request.",
            )
            raise HTTPException(
                status_code=500, detail="Claude Code invocation failed"
            ) from exc

        # Post the response in the thread, splitting long messages
        formatted = md_to_mrkdwn(response.result)
        chunks = split_text(formatted, SLACK_MSG_LIMIT)
        for chunk in chunks:
            await slack_client.chat_postMessage(
                channel=request.channel,
                thread_ts=thread_ts,
                text=chunk,
            )

        return InvokeResponse(
            thread_ts=thread_ts,
            session_id=response.session_id,
            response=response.result,
        )
