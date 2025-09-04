# schemas.py

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
import datetime

# --- Define PostOwner before it is used in PostModel ---
class PostOwner(BaseModel):
    id: int
    login: str
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- Pydantic Schemas for Media ---
class MediaBase(BaseModel):
    filename: str
    original_name: str
    content_type: str
    file_size: int

class MediaModel(MediaBase):
    id: int
    uploaded_at: datetime.datetime
    
    class Config:
        from_attributes = True

class MediaInfo(MediaModel):
    """Extended media info that includes owner information"""
    owner: PostOwner
    
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
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('login')
    def login_validation(cls, v):
        if len(v) < 3:
            raise ValueError('Login must be at least 3 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Login can only contain letters, numbers, hyphens, and underscores')
        return v.lower()

class UserModel(UserBase):
    id: int
    joined_at: datetime.datetime
    is_active: bool = True
    group: Optional[GroupModel] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    group_id: Optional[int] = None
    is_active: Optional[bool] = None

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
    media_id: Optional[int] = None
    
    @validator('clean')
    def clean_validation(cls, v):
        if not v:
            raise ValueError('Slug (clean) is required')
        # Basic slug validation - only lowercase letters, numbers, and hyphens
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        if len(v) < 1:
            raise ValueError('Slug must be at least 1 character long')
        return v
    
    @validator('status')
    def status_validation(cls, v):
        allowed_statuses = ['public', 'private', 'draft']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v
    
    @validator('content_type')
    def content_type_validation(cls, v):
        allowed_types = ['post', 'page']
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v

class PostUpdate(BaseModel):
    content_type: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    parent_id: Optional[int] = None
    feather: Optional[str] = None
    clean: Optional[str] = None
    status: Optional[str] = None
    pinned: Optional[bool] = None
    media_id: Optional[int] = None
    
    @validator('clean')
    def clean_validation(cls, v):
        if v is not None:
            import re
            if not re.match(r'^[a-z0-9-]+$', v):
                raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
            if len(v) < 1:
                raise ValueError('Slug must be at least 1 character long')
        return v
    
    @validator('status')
    def status_validation(cls, v):
        if v is not None:
            allowed_statuses = ['public', 'private', 'draft']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v
    
    @validator('content_type')
    def content_type_validation(cls, v):
        if v is not None:
            allowed_types = ['post', 'page']
            if v not in allowed_types:
                raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v

class PostModel(PostBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    owner: PostOwner
    media: Optional[MediaModel] = None
    
    # Computed properties
    @property
    def has_media(self) -> bool:
        return self.media is not None
    
    @property
    def media_type(self) -> Optional[str]:
        if self.media:
            if self.media.content_type.startswith('image/'):
                return 'image'
            elif self.media.content_type.startswith('audio/'):
                return 'audio'
            elif self.media.content_type.startswith('video/'):
                return 'video'
        return None
    
    class Config:
        from_attributes = True

class PostSummary(BaseModel):
    """Lightweight post model for listings"""
    id: int
    title: Optional[str] = None
    feather: Optional[str] = None
    clean: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    owner: PostOwner
    has_media: bool = False
    
    class Config:
        from_attributes = True

# --- Pydantic Schemas for Authentication ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    login: Optional[str] = None

# --- Response schemas for bulk operations ---
class BulkDeleteResponse(BaseModel):
    deleted_count: int
    message: str

class MediaUploadResponse(BaseModel):
    media: MediaModel
    message: str = "File uploaded successfully"

# --- Validation schemas for forms ---
class PhotoPostCreate(BaseModel):
    clean: str
    title: Optional[str] = None
    status: str = "public"
    
    @validator('clean')
    def clean_validation(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v

class AudioPostCreate(BaseModel):
    clean: str
    title: str
    description: Optional[str] = None
    status: str = "public"
    
    @validator('clean')
    def clean_validation(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v

class VideoPostCreate(BaseModel):
    clean: str
    title: str
    description: Optional[str] = None
    status: str = "public"
    
    @validator('clean')
    def clean_validation(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v

class QuotePostCreate(BaseModel):
    clean: str
    quote: str
    attribution: str
    status: str = "public"
    
    @validator('clean')
    def clean_validation(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v
    
    @validator('quote')
    def quote_validation(cls, v):
        if not v.strip():
            raise ValueError('Quote cannot be empty')
        return v.strip()
    
    @validator('attribution')
    def attribution_validation(cls, v):
        if not v.strip():
            raise ValueError('Attribution cannot be empty')
        return v.strip()

class LinkPostCreate(BaseModel):
    clean: str
    title: str
    url: str
    description: Optional[str] = None
    status: str = "public"
    
    @validator('clean')
    def clean_validation(cls, v):
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return v
    
    @validator('title')
    def title_validation(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('url')
    def url_validation(cls, v):
        if not v.strip():
            raise ValueError('URL cannot be empty')
        # Basic URL validation
        url = v.strip()
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        return url