from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from typing import Dict

security = HTTPBearer()


def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, str]:
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_attorney(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, str]:
    """Require attorney role"""
    current_user = get_current_user(credentials)
    if current_user["role"] != "attorney":
        raise HTTPException(status_code=403, detail="Access denied. Attorney role required.")
    return current_user


def require_client(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, str]:
    """Require client role"""
    current_user = get_current_user(credentials)
    if current_user["role"] != "client":
        raise HTTPException(status_code=403, detail="Access denied. Client role required.")
    return current_user
