from fastapi import Header, HTTPException, Depends
from auth import get_token as auth_token

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401, 
                detail={"error": "Access token required"}
            )
    token = authorization[7:]
    
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