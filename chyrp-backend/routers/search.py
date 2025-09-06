# routers/search.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List

from dependencies import get_db
import models
import schemas
from ai_utils import ai_model 

router = APIRouter(
    tags=["Search"],
)

# ... (The get_ai_suggested_category function remains the same) ...
def get_ai_suggested_category(query: str, db: Session) -> str | None:
    # This function is fine, no changes needed here.
    pass


# Note the change in the response_model
@router.get("/search/posts", response_model=schemas.PaginatedPosts)
def search_posts(
    q: str,
    db: Session = Depends(get_db)
):
    """
    Search for posts based on a query string, enhanced with AI category suggestions.
    """
    if not q:
        # Return the correct empty shape
        return {"posts": []}

    ai_category = get_ai_suggested_category(q, db)
    search_query = f"%{q.lower()}%"
    
    base_filter = [models.Post.status == 'public']
    search_conditions = [
        models.Post.title.ilike(search_query),
        models.Post.body.ilike(search_query),
        models.Post.tags.any(models.Tag.name.ilike(search_query)),
    ]

    if ai_category:
        search_conditions.append(models.Post.categories.any(models.Category.name == ai_category))

    posts = db.query(models.Post).options(
        joinedload(models.Post.tags),
        joinedload(models.Post.categories),
        joinedload(models.Post.owner)
    ).filter(
        *base_filter,
        or_(*search_conditions)
    ).distinct().order_by(models.Post.created_at.desc()).all()

    # Return the data in the format the frontend expects
    return {"posts": posts}