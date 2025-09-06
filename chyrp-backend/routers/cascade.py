# routers/cascade.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
import datetime

from dependencies import get_db, get_optional_current_user
from models import Post, User
import schemas

router = APIRouter(
    tags=["Cascade"],
)

class CascadeService:
    """Infinite scrolling service."""
    
    @staticmethod
    def get_posts_cursor(
        cursor: Optional[str] = None,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        content_type: Optional[str] = None,
        user_id: Optional[int] = None,
        db: Session = Depends(get_db)
    ):
        """Get posts with cursor-based pagination."""
        query = db.query(Post).filter(Post.status == 'public')
        
        # Apply filters
        if content_type:
            query = query.filter(Post.content_type == content_type)
        
        if user_id:
            query = query.filter(Post.user_id == user_id)
        
        # Apply cursor
        if cursor:
            try:
                # Parse cursor (format: "timestamp_id")
                cursor_timestamp, cursor_id = cursor.split('_')
                cursor_datetime = datetime.datetime.fromisoformat(cursor_timestamp)
                
                if sort_order == "desc":
                    query = query.filter(
                        (Post.created_at < cursor_datetime) |
                        ((Post.created_at == cursor_datetime) & (Post.id < int(cursor_id)))
                    )
                else:
                    query = query.filter(
                        (Post.created_at > cursor_datetime) |
                        ((Post.created_at == cursor_datetime) & (Post.id > int(cursor_id)))
                    )
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        
        # Apply sorting
        if sort_by == "created_at":
            if sort_order == "desc":
                query = query.order_by(desc(Post.created_at), desc(Post.id))
            else:
                query = query.order_by(asc(Post.created_at), asc(Post.id))
        elif sort_by == "updated_at":
            if sort_order == "desc":
                query = query.order_by(desc(Post.updated_at), desc(Post.id))
            else:
                query = query.order_by(asc(Post.updated_at), asc(Post.id))
        elif sort_by == "view_count":
            if sort_order == "desc":
                query = query.order_by(desc(Post.view_count), desc(Post.id))
            else:
                query = query.order_by(asc(Post.view_count), asc(Post.id))
        
        # Get posts
        posts = query.limit(limit + 1).all()  # Get one extra to check if there are more
        
        # Check if there are more posts
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
        
        # Generate next cursor
        next_cursor = None
        if has_more and posts:
            last_post = posts[-1]
            next_cursor = f"{last_post.created_at.isoformat()}_{last_post.id}"
        
        return {
            "posts": posts,
            "has_more": has_more,
            "next_cursor": next_cursor,
            "total_returned": len(posts)
        }
    
    @staticmethod
    def get_posts_by_tag_cursor(
        tag_id: int,
        cursor: Optional[str] = None,
        limit: int = 20,
        db: Session = Depends(get_db)
    ):
        """Get posts by tag with cursor-based pagination."""
        from models import Tag
        
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        query = db.query(Post).join(Post.tags).filter(
            Tag.id == tag_id,
            Post.status == 'public'
        )
        
        # Apply cursor
        if cursor:
            try:
                cursor_timestamp, cursor_id = cursor.split('_')
                cursor_datetime = datetime.datetime.fromisoformat(cursor_timestamp)
                
                query = query.filter(
                    (Post.created_at < cursor_datetime) |
                    ((Post.created_at == cursor_datetime) & (Post.id < int(cursor_id)))
                )
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        
        query = query.order_by(desc(Post.created_at), desc(Post.id))
        
        posts = query.limit(limit + 1).all()
        
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
        
        next_cursor = None
        if has_more and posts:
            last_post = posts[-1]
            next_cursor = f"{last_post.created_at.isoformat()}_{last_post.id}"
        
        return {
            "tag_id": tag_id,
            "tag_name": tag.name,
            "posts": posts,
            "has_more": has_more,
            "next_cursor": next_cursor,
            "total_returned": len(posts)
        }
    
    @staticmethod
    def get_posts_by_category_cursor(
        category_id: int,
        cursor: Optional[str] = None,
        limit: int = 20,
        db: Session = Depends(get_db)
    ):
        """Get posts by category with cursor-based pagination."""
        from models import Category
        
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        query = db.query(Post).join(Post.categories).filter(
            Category.id == category_id,
            Post.status == 'public'
        )
        
        # Apply cursor
        if cursor:
            try:
                cursor_timestamp, cursor_id = cursor.split('_')
                cursor_datetime = datetime.datetime.fromisoformat(cursor_timestamp)
                
                query = query.filter(
                    (Post.created_at < cursor_datetime) |
                    ((Post.created_at == cursor_datetime) & (Post.id < int(cursor_id)))
                )
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        
        query = query.order_by(desc(Post.created_at), desc(Post.id))
        
        posts = query.limit(limit + 1).all()
        
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
        
        next_cursor = None
        if has_more and posts:
            last_post = posts[-1]
            next_cursor = f"{last_post.created_at.isoformat()}_{last_post.id}"
        
        return {
            "category_id": category_id,
            "category_name": category.name,
            "posts": posts,
            "has_more": has_more,
            "next_cursor": next_cursor,
            "total_returned": len(posts)
        }

@router.get("/cascade/posts", response_model=dict, tags=["Cascade"])
def get_posts_cascade(
    cursor: Optional[str] = None,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    content_type: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get posts with infinite scrolling support."""
    result = CascadeService.get_posts_cursor(
        cursor=cursor,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        content_type=content_type,
        user_id=user_id,
        db=db
    )
    
    return result

@router.get("/cascade/tags/{tag_id}/posts", response_model=dict, tags=["Cascade"])
def get_posts_by_tag_cascade(
    tag_id: int,
    cursor: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get posts by tag with infinite scrolling support."""
    return CascadeService.get_posts_by_tag_cursor(
        tag_id=tag_id,
        cursor=cursor,
        limit=limit,
        db=db
    )

@router.get("/cascade/categories/{category_id}/posts", response_model=dict, tags=["Cascade"])
def get_posts_by_category_cascade(
    category_id: int,
    cursor: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get posts by category with infinite scrolling support."""
    return CascadeService.get_posts_by_category_cursor(
        category_id=category_id,
        cursor=cursor,
        limit=limit,
        db=db
    )

@router.get("/cascade/user/{user_id}/posts", response_model=dict, tags=["Cascade"])
def get_user_posts_cascade(
    user_id: int,
    cursor: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's posts with infinite scrolling support."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = CascadeService.get_posts_cursor(
        cursor=cursor,
        limit=limit,
        user_id=user_id,
        db=db
    )
    
    result["user_id"] = user_id
    result["user_name"] = user.login
    
    return result
