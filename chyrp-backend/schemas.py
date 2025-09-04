# schemas.py

from pydantic import BaseModel, computed_field
from typing import List, Optional
import datetime

# --- Pydantic Schemas for AI Enhancement ---
class AIEnhanceRequest(BaseModel):
    text: str
    prompt: str = "Fix spelling and grammar, and improve the clarity and flow of the following text:"

class AIEnhanceResponse(BaseModel):
    enhanced_text: str

# --- Define supporting schemas BEFORE they are used ---

class PostOwner(BaseModel):
    id: int
    login: str
    class Config:
        from_attributes = True

# --- NEW: Define UserLikeInfo here, BEFORE PostModel ---
class UserLikeInfo(BaseModel):
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

# --- MODIFIED: The PostModel now correctly handles likes ---
class PostModel(PostBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    owner: PostOwner
    # Now this works because UserLikeInfo is defined above
    liked_by_users: List[UserLikeInfo] = [] 

    @computed_field
    @property
    def likes_count(self) -> int:
        return len(self.liked_by_users)

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
    is_active: bool
    joined_at: datetime.datetime
    group: Optional[GroupModel] = None
    class Config:
        from_attributes = True

# --- Pydantic Schemas for Authentication ---

class TokenData(BaseModel):
    login: Optional[str] = None