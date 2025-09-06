# routers/search.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List

from dependencies import get_db
import models
import schemas

router = APIRouter(
    tags=["Search"],
)

@router.get("/search/posts", response_model=List[schemas.PostModel])
def search_posts(
    q: str,  # The search query from the user
    db: Session = Depends(get_db)
):
    """
    Search for posts based on a query string.
    Searches in post titles, bodies, tag names, and category names.
    """
    if not q:
        return []

    search_query = f"%{q.lower()}%"

    posts = db.query(models.Post).options(
        joinedload(models.Post.tags),
        joinedload(models.Post.categories),
        joinedload(models.Post.owner)
    ).filter(
        models.Post.status == 'public',
        or_(
            models.Post.title.ilike(search_query),
            models.Post.body.ilike(search_query),
            models.Post.tags.any(models.Tag.name.ilike(search_query)),
            models.Post.categories.any(models.Category.name.ilike(search_query))
        )
    ).distinct().all()

    return posts