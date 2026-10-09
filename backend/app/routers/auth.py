import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.auth import create_jwt, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
REDIRECT_URI = "http://localhost:8000/auth/google/callback"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _build_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    # autogenerate_code_verifier=False disables PKCE entirely.
    # This is a confidential server-side client (it has a client_secret), so
    # PKCE is not required. The default True causes a code_verifier to be
    # generated on the /login Flow instance, which is then discarded — the
    # fresh Flow created in /callback has no verifier and the token exchange
    # fails with "Missing code verifier" (or "invalid_request" if None is sent).
    flow = Flow.from_client_config(client_config, scopes=SCOPES, autogenerate_code_verifier=False)
    flow.redirect_uri = REDIRECT_URI
    return flow


@router.get("/google/login")
async def google_login():
    flow = _build_flow()
    auth_url, _state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return RedirectResponse(auth_url, status_code=302)


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    # Handle cases where Google returns an error (e.g. user denied consent)
    if error or not code:
        reason = error or "no_code"
        logger.warning("OAuth callback received error from Google: %s", reason)
        return RedirectResponse(f"{FRONTEND_ORIGIN}/?error={reason}", status_code=302)

    try:
        flow = _build_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
    except Exception as exc:
        logger.exception("Failed to exchange OAuth code for tokens: %s", exc)
        return RedirectResponse(f"{FRONTEND_ORIGIN}/?error=token_exchange_failed", status_code=302)

    try:
        # Fetch user profile from Google
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {credentials.token}"},
            )
            resp.raise_for_status()
            user_info = resp.json()
    except Exception as exc:
        logger.exception("Failed to fetch Google user info: %s", exc)
        return RedirectResponse(f"{FRONTEND_ORIGIN}/?error=userinfo_failed", status_code=302)

    google_id = user_info["sub"]
    email = user_info.get("email", "")
    name = user_info.get("name", "")

    # Calculate token expiry
    token_expiry = None
    if credentials.expiry:
        token_expiry = credentials.expiry

    try:
        # Upsert user — wrapped so any DB failure redirects gracefully
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                token_expiry=token_expiry,
            )
            db.add(user)
        else:
            user.email = email
            user.name = name
            user.access_token = credentials.token
            if credentials.refresh_token:
                user.refresh_token = credentials.refresh_token
            user.token_expiry = token_expiry

        await db.commit()
        await db.refresh(user)
    except Exception as exc:
        logger.exception("Failed to upsert user in database: %s", exc)
        return RedirectResponse(f"{FRONTEND_ORIGIN}/?error=db_error", status_code=302)

    jwt_token = create_jwt(user.id)
    return RedirectResponse(f"{FRONTEND_ORIGIN}/callback?token={jwt_token}", status_code=302)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "google_id": current_user.google_id,
    }


@router.post("/logout")
async def logout():
    return {"message": "Logged out. Clear your JWT on the client."}
