# routers/interactions.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# --- Corrected Imports ---
# Import models from the models.py file
import models
# Import dependencies
from dependencies import get_db, get_current_user, require_permission

router = APIRouter(
    tags=["Interactions"],
)

@router.post("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def toggle_post_like(
    post_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["like_post"]))
):
    """Toggles a like on a post for the current user."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if current_user in post.liked_by_users:
        post.liked_by_users.remove(current_user)
    else:
        post.liked_by_users.append(current_user)
        
    db.commit()

@router.post("/posts/{post_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
def toggle_post_bookmark(
    post_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Toggles a bookmark on a post for the current user."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if current_user in post.bookmarked_by_users:
        post.bookmarked_by_users.remove(current_user)
    else:
        post.bookmarked_by_users.append(current_user)
        
    db.commit()

@router.post("/users/{user_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def toggle_favorite_writer(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Toggles a user as a favorite writer for the current user."""
    user_to_favorite = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_favorite:
        raise HTTPException(status_code=404, detail="User not found")

    if user_to_favorite == current_user:
        raise HTTPException(status_code=400, detail="You cannot favorite yourself")

    if user_to_favorite in current_user.favorites:
        current_user.favorites.remove(user_to_favorite)
    else:
        current_user.favorites.append(user_to_favorite)
        
    db.commit()