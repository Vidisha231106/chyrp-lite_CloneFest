# routers/tags.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import re
import schemas
from dependencies import get_db, get_current_user, require_permission
from models import Tag, Post, User
from schemas import TagModel, PaginatedPosts # <-- EDIT THIS LINE
from cache import cache_for_1_hour, cache_for_5_minutes
from schemas import TagModel, PaginatedPosts

router = APIRouter(
    tags=["Tags"],
)

def create_slug(name: str) -> str:
    """Create a URL-friendly slug from a tag name."""
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^a-z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug

@router.post("/tags", response_model=schemas.TagModel)
def create_tag(
    tag: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["add_post"]))
):
    """Create a new tag."""
    # Check if tag already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag already exists")
    
    # Create slug
    slug = create_slug(tag.name)
    
    # Ensure slug is unique
    counter = 1
    original_slug = slug
    while db.query(Tag).filter(Tag.slug == slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    db_tag = Tag(
        name=tag.name,
        slug=slug,
        description=tag.description,
        color=tag.color
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.get("/tags", response_model=List[schemas.TagModel])
def get_tags(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Get all tags with optional search."""
    query = db.query(Tag)
    
    if search:
        query = query.filter(Tag.name.ilike(f"%{search}%"))
    
    tags = query.offset(skip).limit(limit).all()
    return tags

@router.get("/tags/popular", response_model=List[schemas.TagModel])
def get_popular_tags(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get most popular tags by post count."""
    tags = db.query(Tag).join(Tag.posts).group_by(Tag.id).order_by(
        func.count(Post.id).desc()
    ).limit(limit).all()
    return tags

@router.get("/tags/{tag_id}", response_model=schemas.TagModel)
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    """Get a specific tag by ID."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.get("/tags/slug/{slug}", response_model=schemas.TagModel)
def get_tag_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a tag by its slug."""
    tag = db.query(Tag).filter(Tag.slug == slug).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/tags/{tag_id}", response_model=schemas.TagModel)
def update_tag(
    tag_id: int,
    tag_update: schemas.TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["edit_post"]))
):
    """Update a tag."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Update fields if provided
    if tag_update.name is not None:
        # Check if new name conflicts with existing tag
        existing_tag = db.query(Tag).filter(Tag.name == tag_update.name, Tag.id != tag_id).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail="Tag name already exists")
        tag.name = tag_update.name
        tag.slug = create_slug(tag_update.name)
    
    if tag_update.description is not None:
        tag.description = tag_update.description
    
    if tag_update.color is not None:
        tag.color = tag_update.color
    
    db.commit()
    db.refresh(tag)
    return tag

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["delete_post"]))
):
    """Delete a tag."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    db.delete(tag)
    db.commit()
    return

@router.post("/posts/{post_id}/tags/{tag_id}", response_model=schemas.PostModel)
def add_tag_to_post(
    post_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a tag to a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions - user can edit if they have edit_post OR if they own the post and have edit_own_post
    user_permissions = current_user.group.permissions
    can_edit_any = "edit_post" in user_permissions
    can_edit_own = "edit_own_post" in user_permissions and post.user_id == current_user.id
    
    if not (can_edit_any or can_edit_own):
        raise HTTPException(status_code=403, detail="You do not have permission to edit this post")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if tag not in post.tags:
        post.tags.append(tag)
        db.commit()
    
    db.refresh(post)
    return post

@router.delete("/posts/{post_id}/tags/{tag_id}", response_model=schemas.PostModel)
def remove_tag_from_post(
    post_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["edit_post", "edit_own_post"]))
):
    """Remove a tag from a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions
    if post.user_id != current_user.id and "edit_post" not in current_user.group.permissions:
        raise HTTPException(status_code=403, detail="You can only edit your own posts")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if tag in post.tags:
        post.tags.remove(tag)
        db.commit()
    
    db.refresh(post)
    return post

@router.get("/tags/{tag_id}/posts", response_model=PaginatedPosts)
def get_posts_by_tag(
    tag_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all public posts with a specific tag."""
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Add a filter for Post.status
    posts = db.query(Post).join(Post.tags).filter(
        Tag.id == tag_id,
        Post.status == 'public' # <-- ADD THIS LINE
    ).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    
    # Return the data in the format the frontend expects
    return {"posts": posts}

@router.post("/tags/get-or-create", response_model=List[schemas.TagModel])
def get_or_create_tags(
    tag_names: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get existing tags or create new ones for a list of tag names."""
    final_tags = []
    for name in tag_names:
        name = name.strip()
        if not name:
            continue
        db_tag = db.query(Tag).filter(Tag.name.ilike(name)).first()
        if not db_tag:
            db_tag = Tag(name=name, slug=create_slug(name))
            db.add(db_tag)
            db.commit()
            db.refresh(db_tag)
        final_tags.append(db_tag)
    return final_tags