"""LTI 1.3 claim extraction and role mapping."""

from dataclasses import dataclass

LTI_CLAIM_ROLES = "https://purl.imsglobal.org/spec/lti/claim/roles"
LTI_CLAIM_CONTEXT = "https://purl.imsglobal.org/spec/lti/claim/context"
LTI_CLAIM_RESOURCE_LINK = "https://purl.imsglobal.org/spec/lti/claim/resource_link"

# Priority order: admin > faculty > student
_ROLE_MAP = [
    ("institution/person#Administrator", "admin"),
    ("membership#Instructor", "faculty"),
    ("membership#Learner", "student"),
]


def map_lti_role(roles: list[str]) -> str:
    """Map LTI role URNs to internal role. Highest priority wins."""
    for pattern, internal_role in _ROLE_MAP:
        if any(pattern in r for r in roles):
            return internal_role
    return "student"


@dataclass
class LtiClaims:
    """Parsed LTI 1.3 launch claims."""

    lti_user_id: str
    user_name: str | None
    user_email: str | None
    role: str
    course_id: str | None
    course_label: str | None
    course_title: str | None
    resource_link_id: str | None


def extract_lti_claims(payload: dict) -> LtiClaims:
    """Extract structured claims from a validated LTI id_token payload."""
    roles = payload.get(LTI_CLAIM_ROLES, [])
    context = payload.get(LTI_CLAIM_CONTEXT, {})
    resource_link = payload.get(LTI_CLAIM_RESOURCE_LINK, {})

    return LtiClaims(
        lti_user_id=payload["sub"],
        user_name=payload.get("name"),
        user_email=payload.get("email"),
        role=map_lti_role(roles),
        course_id=context.get("id"),
        course_label=context.get("label"),
        course_title=context.get("title"),
        resource_link_id=resource_link.get("id"),
    )
