# schemas.py

from pydantic import BaseModel
from typing import List, Optional
import datetime

# --- MOVED: Define PostOwner before it is used in PostModel ---
class PostOwner(BaseModel):
    id: int
    login: str
    class Config:
        from_attributes = True

# --- Pydantic Schemas for Posts/Pages ---

class PostBase(BaseModel):
    content_type: str = "post"
    title: Optional[str] = None
    body: Optional[str] = None
    parent_id: Optional[int] = None
    feather: Optional[str] = None
    clean: str
    status: str = "public"
    pinned: bool = False

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content_type: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    parent_id: Optional[int] = None
    feather: Optional[str] = None
    clean: Optional[str] = None
    status: Optional[str] = None
    pinned: Optional[bool] = None

class PostModel(PostBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    owner: PostOwner # Now this works because PostOwner is defined above
    class Config:
        from_attributes = True

# --- Pydantic Schemas for Groups ---

class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    permissions: List[str] = []

class GroupModel(GroupBase):
    id: int
    permissions: List[str]
    class Config:
        from_attributes = True

# --- Pydantic Schemas for Users ---

class UserBase(BaseModel):
    login: str
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserModel(UserBase):
    id: int
    joined_at: datetime.datetime
    # --- REMOVED: 'posts' list to simplify and prevent circular dependencies ---
    group: Optional[GroupModel] = None
    class Config:
        from_attributes = True

# --- Pydantic Schemas for Authentication ---

class TokenData(BaseModel):
    login: Optional[str] = None

