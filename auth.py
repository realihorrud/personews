import os

import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

CLERK_JWKS_URL = os.getenv('CLERK_JWKS_URL')

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    token = credentials.credentials
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(CLERK_JWKS_URL)
            jwks = resp.json()
        payload = jwt.decode(token, jwks, algorithms=["RS256"])
        return payload
    except JWTError as err:
        raise HTTPException(status_code=401, detail="Invalid or expired token")