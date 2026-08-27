from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth import get_token as auth_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if credentials is None:
        raise HTTPException(status_code=401, detail={"error": "Access token required"})

    token = credentials.credentials

    try:
        result = auth_token(token)
        user = result.user
        return {
            "id": user.id,
            "email": user.email,
            "created_at": str(user.created_at)
        }
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or Expired Token!"})