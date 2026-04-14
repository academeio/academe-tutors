"""LTI 1.3 launch and service endpoints.

Handles OIDC login, JWT validation, and deep linking.
Canvas launches Academe Tutors via this router.
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/login")
async def oidc_login(request: Request):
    """OIDC login initiation — Canvas redirects here first."""
    # TODO: Implement pylti1p3 OIDC login flow
    # 1. Validate login_hint, target_link_uri from Canvas
    # 2. Build OIDC auth redirect URL
    # 3. Redirect to Canvas authorization endpoint
    return {"status": "not_implemented", "step": "oidc_login"}


@router.post("/launch")
async def lti_launch(request: Request):
    """LTI 1.3 resource link launch — Canvas POST after OIDC completes.

    Flow:
    1. Validate id_token JWT (signed by Canvas)
    2. Extract launch context (user, course, resource, roles)
    3. Create or resume tutor session
    4. Redirect to frontend chat UI with session token
    """
    # TODO: Implement pylti1p3 launch validation
    # 1. Validate JWT signature against Canvas JWKS
    # 2. Extract claims: sub, name, email, roles, context (course)
    # 3. Resolve tenant from platform URL
    # 4. Find or create tutor_session
    # 5. Find or create tutor_profile
    # 6. Redirect to frontend: /chat?session={session_id}&token={jwt}
    return {"status": "not_implemented", "step": "lti_launch"}


@router.get("/jwks")
async def jwks():
    """Public JWKS endpoint — Canvas fetches our public keys for message signing."""
    # TODO: Return tool's public key set
    return {"keys": []}
