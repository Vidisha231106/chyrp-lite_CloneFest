# dependencies.py

import datetime
from typing import List, Optional # Ensure List is imported

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import models
import schemas
from database import SessionLocal

# --- Configuration ---
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Re-usable Components & Utilities ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_scheme = APIKeyHeader(name="Authorization")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(api_key_scheme), db: Session = Depends(get_db)):
    try:
        token_type, token_value = token.split()
        if token_type.lower() != "bearer":
            raise ValueError("Invalid token type")
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            raise credentials_exception
        token_data = schemas.TokenData(login=login)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.login == token_data.login).first()
    if user is None:
        raise credentials_exception
    return user

async def get_optional_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current user if authenticated, otherwise return None."""
    # Get Authorization header manually
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        token_type, token_value = auth_header.split()
        if token_type.lower() != "bearer":
            return None
    except (ValueError, AttributeError):
        return None
    
    try:
        payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            return None
        token_data = schemas.TokenData(login=login)
    except JWTError:
        return None
    
    user = db.query(models.User).filter(models.User.login == token_data.login).first()
    return user

# --- NEW: Add the missing permission dependency function ---
def require_permission(required_permissions: List[str]):
    """
    This is a dependency factory. It creates and returns a dependency function
    that checks if the current user has ALL of the required permissions.
    """
    def permission_checker(current_user: models.User = Depends(get_current_user)):
        user_permissions = current_user.group.permissions
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have the required permission: {permission}",
                )
    return permission_checker

def require_post_permission(perm_any: str, perm_own: str):
    """
    Dependency factory to check for post-related permissions.
    Checks if user has the 'perm_any' or if they are the owner and have 'perm_own'.
    """
    def checker(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
        # Get the post from the database
        db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
        if db_post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
            
        user_permissions = current_user.group.permissions
        
        # Check for general permission (e.g., 'edit_post')
        if perm_any in user_permissions:
            return db_post # Permission granted, return the post object for the endpoint to use
            
        # Check for ownership and owner-specific permission (e.g., 'edit_own_post')
        is_owner = db_post.user_id == current_user.id
        if is_owner and perm_own in user_permissions:
            return db_post # Permission granted, return the post object

        # If neither check passes, deny access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to perform this action.",
        )
    return checker

# Remove duplicate function - already defined above