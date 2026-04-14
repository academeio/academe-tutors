"""Seed lti_platforms for SBV Canvas installation."""
import asyncio
import os

import asyncpg


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"].replace("+asyncpg", ""))
    await conn.execute("""
        INSERT INTO lti_platforms (issuer, client_id, auth_url, jwks_url, token_url, tenant_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (issuer) DO UPDATE SET
            client_id = EXCLUDED.client_id,
            auth_url = EXCLUDED.auth_url,
            jwks_url = EXCLUDED.jwks_url,
            token_url = EXCLUDED.token_url
    """,
        "https://canvas.instructure.com",  # All Canvas Cloud instances use this issuer
        os.environ.get("LTI_CLIENT_ID", "FILL_AFTER_DEV_KEY_CREATED"),
        "https://sbvlms.cloudintegral.com/api/lti/authorize_redirect",
        "https://sbvlms.cloudintegral.com/api/lti/security/jwks",
        "https://sbvlms.cloudintegral.com/login/oauth2/token",
        1,  # SBV tenant_id
    )
    print("Seeded SBV LTI platform")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
