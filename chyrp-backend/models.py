# models.py

from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Table, JSON, Boolean)  # Add Boolean import
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
    body = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="posts")
    parent = relationship("Post", remote_side=[id], back_populates="children")
    children = relationship("Post", back_populates="parent")
    
    liked_by_users = relationship("User", secondary=post_likes_association, back_populates="liked_posts")
    bookmarked_by_users = relationship("User", secondary=post_bookmarks_association, back_populates="bookmarked_posts")