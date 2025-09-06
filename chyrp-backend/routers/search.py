# routers/search.py

from fastapi import APIRouter, Depends # <-- 1. Corrected typo here
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List
from ai_utils import ai_model
from dependencies import get_db
import models
import schemas

router = APIRouter( # <-- 2. Corrected typo here
    tags=["Search"],
)

def get_ai_suggested_category(query: str, db: Session) -> str | None:
    """
    Uses the Gemini API to find the most relevant category for a search query.
    """
    if not ai_model:
        return None 

    categories = db.query(models.Category.name).all()
    category_names = [c[0] for c in categories]
    
    if not category_names:
        return None

    prompt = f"""
    You are a helpful blog assistant. Your task is to match a user's search query to the most relevant blog category from a given list.

    User Search Query: "{query}"

    Available Categories: {category_names}

    Based on the query, which is the single most relevant category from the list? Respond with only the exact category name and nothing else. If no category is relevant, respond with the word "None".
    """

    try:
        response = ai_model.generate_content(prompt)
        ai_category_name = response.text.strip()
        
        if ai_category_name in category_names:
            print(f"AI suggested category '{ai_category_name}' for query '{query}'")
            return ai_category_name
        else:
            return None
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None


@router.get("/search/posts", response_model=List[schemas.PostModel])
def search_posts(
    q: str,
    db: Session = Depends(get_db)
):
    """
    Search for posts based on a query string, enhanced with AI category suggestions.
    """
    if not q:
        return []

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
    ).distinct().all()

    return posts