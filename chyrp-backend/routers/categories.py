# routers/categories.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import re
import schemas
from dependencies import get_db, get_current_user, require_permission
from models import Category, Post, User
from schemas import CategoryModel, PaginatedPosts # <-- EDIT THIS LINE
from cache import cache_for_1_hour, cache_for_5_minutes

router = APIRouter(
    tags=["Categories"],
)

def create_slug(name: str) -> str:
    """Create a URL-friendly slug from a category name."""
    slug = re.sub(r'[^a-z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug

@router.post("/categories", response_model=schemas.CategoryModel)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["add_post"]))
):
    """Create a new category."""
    existing_category = db.query(Category).filter(Category.name == category.name).first()
    if existing_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    if category.parent_id:
        parent_category = db.query(Category).filter(Category.id == category.parent_id).first()
        if not parent_category:
            raise HTTPException(status_code=404, detail="Parent category not found")
    
    slug = create_slug(category.name)
    counter = 1
    original_slug = slug
    while db.query(Category).filter(Category.slug == slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    db_category = Category(
        name=category.name,
        slug=slug,
        description=category.description,
        color=category.color,
        parent_id=category.parent_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories", response_model=List[schemas.CategoryModel])
@cache_for_1_hour()
def get_categories(
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    parent_id: int = None,
    db: Session = Depends(get_db)
):
    """Get all categories with optional search and parent filtering."""
    query = db.query(Category)
    
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    
    if parent_id is not None:
        if parent_id == 0:
            query = query.filter(Category.parent_id.is_(None))
        else:
            query = query.filter(Category.parent_id == parent_id)
    
    categories = query.offset(skip).limit(limit).all()
    return categories

@router.get("/categories/tree", response_model=List[schemas.CategoryModel])
@cache_for_1_hour()
def get_category_tree(db: Session = Depends(get_db)):
    """Get categories in a hierarchical tree structure."""
    all_categories = db.query(Category).all()
    category_dict = {cat.id: schemas.CategoryModel.from_orm(cat) for cat in all_categories}
    
    root_categories = []
    for category in all_categories:
        if category.parent_id is None:
            root_categories.append(category_dict[category.id])
        else:
            if category.parent_id in category_dict:
                parent = category_dict[category.parent_id]
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(category_dict[category.id])
    
    return root_categories

@router.get("/categories/popular", response_model=List[schemas.CategoryModel])
def get_popular_categories(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get most popular categories by post count."""
    categories = db.query(Category).join(Category.posts).group_by(Category.id).order_by(
        func.count(Post.id).desc()
    ).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=schemas.CategoryModel)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category by ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.get("/categories/slug/{slug}", response_model=schemas.CategoryModel)
def get_category_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a category by its slug."""
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/categories/{category_id}", response_model=schemas.CategoryModel)
def update_category(
    category_id: int,
    category_update: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["edit_post"]))
):
    """Update a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category_update.name is not None:
        existing_category = db.query(Category).filter(
            Category.name == category_update.name, 
            Category.id != category_id
        ).first()
        if existing_category:
            raise HTTPException(status_code=400, detail="Category name already exists")
        category.name = category_update.name
        category.slug = create_slug(category_update.name)
    
    if category_update.description is not None:
        category.description = category_update.description
    
    if category_update.color is not None:
        category.color = category_update.color
    
    if category_update.parent_id is not None:
        if category_update.parent_id != 0:
            parent_category = db.query(Category).filter(Category.id == category_update.parent_id).first()
            if not parent_category:
                raise HTTPException(status_code=404, detail="Parent category not found")
            if category_update.parent_id == category_id:
                raise HTTPException(status_code=400, detail="Category cannot be its own parent")
        category.parent_id = category_update.parent_id if category_update.parent_id != 0 else None
    
    db.commit()
    db.refresh(category)
    return category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["delete_post"]))
):
    """Delete a category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    children = db.query(Category).filter(Category.parent_id == category_id).count()
    if children > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete category with child categories. Delete children first."
        )
    
    db.delete(category)
    db.commit()
    return

@router.post("/posts/{post_id}/categories/{category_id}", response_model=schemas.PostModel)
def add_category_to_post(
    post_id: int,
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a category to a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions - user can edit if they have edit_post OR if they own the post and have edit_own_post
    user_permissions = current_user.group.permissions
    can_edit_any = "edit_post" in user_permissions
    can_edit_own = "edit_own_post" in user_permissions and post.user_id == current_user.id
    
    if not (can_edit_any or can_edit_own):
        raise HTTPException(status_code=403, detail="You do not have permission to edit this post")
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category not in post.categories:
        post.categories.append(category)
        db.commit()
    
    db.refresh(post)
    return post

@router.delete("/posts/{post_id}/categories/{category_id}", response_model=schemas.PostModel)
def remove_category_from_post(
    post_id: int,
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(["edit_post", "edit_own_post"]))
):
    """Remove a category from a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id and "edit_post" not in current_user.group.permissions:
        raise HTTPException(status_code=403, detail="You can only edit your own posts")
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category in post.categories:
        post.categories.remove(category)
        db.commit()
    
    db.refresh(post)
    return post

@router.get("/categories/{category_id}/posts", response_model=PaginatedPosts)
def get_posts_by_category(
    category_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all public posts with a specific category."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Add a filter for Post.status
    posts = db.query(Post).join(Post.categories).filter(
        Category.id == category_id,
        Post.status == 'public' # <-- ADD THIS LINE
    ).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    
    # Return the data in the format the frontend expects
    return {"posts": posts}

@router.get("/categories/for-dropdown", response_model=List[schemas.CategoryModel])
def get_categories_for_dropdown(db: Session = Depends(get_db)):
    """Get all categories for dropdown selection (no pagination)."""
    categories = db.query(Category).order_by(Category.name).all()
    return categories