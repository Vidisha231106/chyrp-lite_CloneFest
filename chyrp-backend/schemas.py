from pydantic import BaseModel, computed_field
from typing import List, Optional
import datetime

# ------------------------
# Authentication Schemas
# ------------------------
class TokenData(BaseModel):
    login: Optional[str] = None

# ------------------------
# Group Schemas
# ------------------------
class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    permissions: List[str] = []

class GroupModel(GroupBase):
    id: int
    permissions: List[str]

    class Config:
        from_attributes = True


# ------------------------
# User Schemas
# ------------------------
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


# ------------------------
# Tag Schemas
# ------------------------
class TagBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class TagModel(TagBase):
    id: int
    slug: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ------------------------
# Category Schemas
# ------------------------
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryModel(CategoryBase):
    id: int
    slug: str
    created_at: datetime.datetime
    children: List["CategoryModel"] = []

    class Config:
        from_attributes = True

# allow nested categories
CategoryModel.model_rebuild()


# ------------------------
# Comment Schemas
# ------------------------
class CommentAuthor(BaseModel):
    id: int
    login: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: str

class CommentModel(CommentBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_approved: bool
    author: CommentAuthor
    replies: List["CommentModel"] = []

    class Config:
        from_attributes = True

# allow nested replies
CommentModel.model_rebuild()


# ------------------------
# Post Schemas
# ------------------------
class PostOwner(BaseModel):
    id: int
    login: str

    class Config:
        from_attributes = True

class UserLikeInfo(BaseModel):
    id: int
    login: str

    class Config:
        from_attributes = True

class PostBase(BaseModel):
    content_type: str = "post"
    title: Optional[str] = None
    body: Optional[str] = None
    excerpt: Optional[str] = None
    parent_id: Optional[int] = None
    feather: Optional[str] = None
    clean: str
    status: str = "public"
    pinned: bool = False
    rights_attribution: Optional[str] = None
    rights_license: Optional[str] = None
    rights_url: Optional[str] = None

class PostCreate(PostBase):
    tags: List[str] = []
    category_ids: List[int] = []

class PostUpdate(BaseModel):
    content_type: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    excerpt: Optional[str] = None
    parent_id: Optional[int] = None
    feather: Optional[str] = None
    clean: Optional[str] = None
    status: Optional[str] = None
    pinned: Optional[bool] = None
    tag_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None
    rights_attribution: Optional[str] = None
    rights_license: Optional[str] = None
    rights_url: Optional[str] = None

class PostModel(PostBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    owner: PostOwner
    liked_by_users: List[UserLikeInfo] = []
    tags: List[TagModel] = []
    categories: List[CategoryModel] = []
    comments: List["CommentModel"] = []  # <-- ADD THIS LINE

    @computed_field
    @property
    def likes_count(self) -> int:
        return len(self.liked_by_users)

    @computed_field
    @property
    def comments_count(self) -> int:
        return len(self.comments)

    class Config:
        from_attributes = True


# ------------------------
# Post Views
# ------------------------
class PostViewBase(BaseModel):
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class PostViewCreate(PostViewBase):
    pass

class PostViewModel(PostViewBase):
    id: int
    post_id: int
    user_id: Optional[int] = None
    viewed_at: datetime.datetime

    class Config:
        from_attributes = True

class PostViewStats(BaseModel):
    total_views: int
    unique_views: int
    views_today: int
    views_this_week: int
    views_this_month: int


# ------------------------
# AI Enhancement Schemas
# ------------------------
class AIEnhanceRequest(BaseModel):
    text: str
    prompt: str = "Fix spelling and grammar, and improve clarity of the following text:"

class AIEnhanceResponse(BaseModel):
    enhanced_text: str


class PaginatedPosts(BaseModel):
    posts: List[PostModel]
    next_cursor: Optional[int] = None

# In schemas.py, add these new classes at the end of the file

class CascadePostsResponse(BaseModel):
    posts: List[PostModel]
    has_more: bool
    next_cursor: Optional[str] = None
    total_returned: int

class CascadeTagPostsResponse(CascadePostsResponse):
    tag_id: int
    tag_name: str

class CascadeCategoryPostsResponse(CascadePostsResponse):
    category_id: int
    category_name: str

class CascadeUserPostsResponse(CascadePostsResponse):
    user_id: int
    user_name: str

class CommentCreateWithMaptcha(CommentCreate):
    maptcha_challenge_id: str
    maptcha_answer: str