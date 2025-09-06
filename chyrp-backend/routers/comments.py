# routers/comments.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import datetime

from dependencies import get_db, get_current_user, get_optional_current_user, require_permission
from models import Comment, Post, User
import schemas

router = APIRouter(
    tags=["Comments"],
)

@router.post("/posts/{post_id}/comments", response_model=schemas.CommentModel)
def create_comment(
    post_id: int,
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on a post."""
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if parent comment exists (for nested comments)
    if comment.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if not parent_comment or parent_comment.post_id != post_id:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    # Create comment
    db_comment = Comment(
        content=comment.content,
        post_id=post_id,
        user_id=current_user.id,
        parent_id=comment.parent_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/posts/{post_id}/comments", response_model=List[schemas.CommentModel])
def get_post_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_current_user)
):
    """Get all comments for a post (with nested replies)."""
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get top-level comments (no parent)
    comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id.is_(None),
        Comment.is_approved == True
    ).order_by(Comment.created_at.asc()).all()
    
    return comments

@router.get("/comments/{comment_id}", response_model=schemas.CommentModel)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_current_user)
):
    """Get a specific comment by ID."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return comment

@router.put("/comments/{comment_id}", response_model=schemas.CommentModel)
def update_comment(
    comment_id: int,
    comment_update: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only by the author or admin)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author or has admin permissions
    if comment.user_id != current_user.id:
        # Check if user has admin permissions
        if "edit_post" not in current_user.group.permissions:
            raise HTTPException(
                status_code=403, 
                detail="You can only edit your own comments"
            )
    
    comment.content = comment_update.content
    comment.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return comment

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (only by the author or admin)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author or has admin permissions
    if comment.user_id != current_user.id:
        # Check if user has admin permissions
        if "delete_post" not in current_user.group.permissions:
            raise HTTPException(
                status_code=403, 
                detail="You can only delete your own comments"
            )
    
    db.delete(comment)
    db.commit()
    return

@router.post("/comments/{comment_id}/approve", response_model=schemas.CommentModel)
def approve_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["edit_post"]))
):
    """Approve a comment (admin only)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_approved = True
    comment.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return comment

@router.post("/comments/{comment_id}/disapprove", response_model=schemas.CommentModel)
def disapprove_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["edit_post"]))
):
    """Disapprove a comment (admin only)."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_approved = False
    comment.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(comment)
    return comment
