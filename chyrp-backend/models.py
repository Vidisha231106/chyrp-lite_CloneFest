# models.py

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Table, JSON, Boolean, Text, Index)  # Add Text and Index for PostgreSQL optimization
from sqlalchemy.orm import relationship
from database import Base
import datetime

# --- Association Tables for Many-to-Many Relationships ---

post_likes_association = Table('post_likes', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True)
)

post_bookmarks_association = Table('post_bookmarks', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True)
)

favorite_writers_association = Table('favorite_writers', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('favorite_user_id', Integer, ForeignKey('users.id'), primary_key=True)
)

post_tags_association = Table('post_tags', Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

post_categories_association = Table('post_categories', Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

# --- Main Database Models ---

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    permissions = Column(JSON, default=[])
    users = relationship("User", back_populates="group")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True) # <-- ADD THIS LINE
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="users")
    
    posts = relationship("Post", back_populates="owner")
    comments = relationship("Comment", back_populates="author")
    
    liked_posts = relationship("Post", secondary=post_likes_association, back_populates="liked_by_users")
    bookmarked_posts = relationship("Post", secondary=post_bookmarks_association, back_populates="bookmarked_by_users")
    
    favorites = relationship(
        "User",
        secondary=favorite_writers_association,
        primaryjoin=id==favorite_writers_association.c.user_id,
        secondaryjoin=id==favorite_writers_association.c.favorite_user_id,
        back_populates="favorited_by"
    )
    favorited_by = relationship(
        "User",
        secondary=favorite_writers_association,
        primaryjoin=id==favorite_writers_association.c.favorite_user_id,
        secondaryjoin=id==favorite_writers_association.c.user_id,
        back_populates="favorites"
    )

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String, default="post", index=True)
    feather = Column(String, nullable=True)
    clean = Column(String, unique=True, index=True)
    status = Column(String, default="public")
    pinned = Column(Boolean, default=False)  # Changed from Integer to Boolean
    title = Column(String, nullable=True)
    body = Column(Text, nullable=True)  # Use Text for better PostgreSQL performance
    excerpt = Column(Text, nullable=True)  # Auto-generated excerpt for Read More
    parent_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    view_count = Column(Integer, default=0)  # Track post views
    # Rights / attribution
    rights_attribution = Column(String, nullable=True)
    rights_license = Column(String, nullable=True)
    rights_url = Column(String, nullable=True)
    
    owner = relationship("User", back_populates="posts")
    parent = relationship("Post", remote_side=[id], back_populates="children")
    children = relationship("Post", back_populates="parent")
    
    liked_by_users = relationship("User", secondary=post_likes_association, back_populates="liked_posts")
    bookmarked_by_users = relationship("User", secondary=post_bookmarks_association, back_populates="bookmarked_posts")
    
    # Comments relationship
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    
    # Tags relationship
    tags = relationship("Tag", secondary=post_tags_association, back_populates="posts")
    
    # Categories relationship
    categories = relationship("Category", secondary=post_categories_association, back_populates="posts")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # Use Text for better PostgreSQL performance
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_approved = Column(Boolean, default=True)  # For moderation
    
    # Foreign keys
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For nested comments
    
    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)  # URL-friendly version
    description = Column(String, nullable=True)
    color = Column(String, nullable=True)  # For UI styling
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", secondary=post_tags_association, back_populates="tags")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)  # URL-friendly version
    description = Column(String, nullable=True)
    color = Column(String, nullable=True)  # For UI styling
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # For hierarchical categories
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", secondary=post_categories_association, back_populates="categories")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")


class PostView(Base):
    __tablename__ = "post_views"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous views
    ip_address = Column(String, nullable=True)  # Track IP for anonymous views
    user_agent = Column(String, nullable=True)  # Track browser info
    viewed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    post = relationship("Post")
    user = relationship("User")