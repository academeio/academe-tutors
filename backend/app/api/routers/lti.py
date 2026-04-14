"""LTI 1.3 launch and service endpoints."""

import json
import uuid

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from jose import jwt as jose_jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.lti.oidc import (
    get_platform_by_issuer,
    get_platform_jwks,
    generate_state_nonce,
    build_auth_redirect_url,
)
from app.lti.claims import extract_lti_claims
from app.lti.session import create_session_token

router = APIRouter()


@router.api_route("/login", methods=["GET", "POST"])
async def oidc_login(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """OIDC login initiation — Canvas sends GET or POST here."""
    # Canvas may send params as query string (GET) or form body (POST)
    if request.method == "POST":
        form = await request.form()
        params = dict(form)
    else:
        params = dict(request.query_params)

    iss = params.get("iss")
    login_hint = params.get("login_hint")
    target_link_uri = params.get("target_link_uri")
    lti_message_hint = params.get("lti_message_hint")
    client_id = params.get("client_id")

    if not iss or not login_hint:
        raise HTTPException(400, "Missing iss or login_hint")

    platform = await get_platform_by_issuer(db, iss)
    if not platform:
        raise HTTPException(400, f"Unknown platform: {iss}")

    state, nonce = generate_state_nonce()
    # Use the public-facing URL (request.url_for gives internal Railway hostname)
    base = str(request.base_url).rstrip("/")
    if "0.0.0.0" in base or "127.0.0.1" in base or "railway.internal" in base:
        base = f"https://{request.headers.get('host', 'backend.tutor.ai.in')}"
    redirect_uri = f"{base}/lti/launch"

    auth_url = build_auth_redirect_url(
        platform=platform,
        redirect_uri=redirect_uri,
        login_hint=login_hint,
        state=state,
        nonce=nonce,
        lti_message_hint=lti_message_hint,
    )

    response = RedirectResponse(url=auth_url, status_code=302)
    response.set_cookie(
        key="lti_state",
        value=json.dumps({"state": state, "nonce": nonce}),
        max_age=300,
        httponly=True,
        secure=True,
        samesite="none",
    )
    return response


@router.post("/launch")
async def lti_launch(
    request: Request,
    id_token: str = Form(...),
    state: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """LTI 1.3 resource link launch — Canvas POST after OIDC completes."""
    # 1. Verify state from cookie
    state_cookie = request.cookies.get("lti_state")
    if not state_cookie:
        raise HTTPException(400, "Missing state cookie")
    try:
        saved = json.loads(state_cookie)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid state cookie")
    if saved.get("state") != state:
        raise HTTPException(400, "State mismatch")

    # 2. Decode JWT header to get kid, then find issuer from unverified payload
    try:
        unverified = jose_jwt.get_unverified_claims(id_token)
        header = jose_jwt.get_unverified_header(id_token)
    except JWTError:
        raise HTTPException(400, "Malformed id_token")

    issuer = unverified.get("iss")
    platform = await get_platform_by_issuer(db, issuer)
    if not platform:
        raise HTTPException(400, f"Unknown issuer: {issuer}")

    # 3. Fetch JWKS and validate
    jwks = await get_platform_jwks(db, platform)
    kid = header.get("kid")
    matching_keys = [k for k in jwks.get("keys", []) if k.get("kid") == kid]
    if not matching_keys:
        raise HTTPException(400, "No matching key in JWKS")

    try:
        payload = jose_jwt.decode(
            id_token,
            matching_keys[0],
            algorithms=["RS256"],
            audience=platform["client_id"],
            issuer=platform["issuer"],
        )
    except JWTError as e:
        raise HTTPException(400, f"JWT validation failed: {e}")

    # 4. Verify nonce
    if payload.get("nonce") != saved.get("nonce"):
        raise HTTPException(400, "Nonce mismatch")

    # 5. Extract claims
    claims = extract_lti_claims(payload)

    # 6. Create session
    session_id = str(uuid.uuid4())

    # 7. Mint session JWT
    token = create_session_token(
        session_id=session_id,
        user_email=claims.user_email or f"{claims.lti_user_id}@lti",
        tenant_id=platform.get("tenant_id", 1),
        course_id=int(claims.course_id) if claims.course_id else None,
        role=claims.role,
        secret=settings.secret_key,
    )

    # 8. Redirect to frontend
    response = RedirectResponse(
        url=f"{settings.frontend_url}/chat?token={token}",
        status_code=302,
    )
    response.delete_cookie("lti_state")
    return response


@router.get("/jwks")
async def jwks():
    """Public JWKS endpoint — empty for S1, needed for AGS in S3."""
    return {"keys": []}
