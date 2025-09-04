# models.py

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Table, JSON, Boolean, LargeBinary, Text)
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

# --- Main Database Models ---

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    permissions = Column(JSON, default=list)
    
    # Relationships
    users = relationship("User", back_populates="group")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Foreign Keys
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    
    # Relationships
    group = relationship("Group", back_populates="users")
    posts = relationship("Post", back_populates="owner", cascade="all, delete-orphan")
    uploaded_media = relationship("Media", back_populates="owner", cascade="all, delete-orphan")
    
    # Many-to-many relationships
    liked_posts = relationship("Post", secondary=post_likes_association, back_populates="liked_by_users")
    bookmarked_posts = relationship("Post", secondary=post_bookmarks_association, back_populates="bookmarked_by_users")
    
    # Self-referential many-to-many for favorite writers
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

class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)
    file_url = Column(String(1024), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="uploaded_media")
    posts = relationship("Post", back_populates="media")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(50), default="post", index=True, nullable=False)  # "post" or "page"
    feather = Column(String(50), nullable=True)  # Post type: "text", "photo", "quote", "link", "audio", "video", etc.
    clean = Column(String(255), unique=True, index=True, nullable=False)  # URL slug
    status = Column(String(50), default="public", nullable=False)  # "public", "private", "draft"
    pinned = Column(Boolean, default=False)
    title = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)  # Use Text for longer content
    parent_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="posts")
    parent = relationship("Post", remote_side=[id], back_populates="children")
    children = relationship("Post", back_populates="parent", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="posts")
    
    # Many-to-many relationships
    liked_by_users = relationship("User", secondary=post_likes_association, back_populates="liked_posts")
    bookmarked_by_users = relationship("User", secondary=post_bookmarks_association, back_populates="bookmarked_posts")
    
    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title}', feather='{self.feather}')>"