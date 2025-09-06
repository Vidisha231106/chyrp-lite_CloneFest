# routers/views.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List
import datetime

from dependencies import get_db, get_optional_current_user
from models import Post, PostView, User
import schemas

router = APIRouter(
    tags=["Views"],
)

@router.post("/views/posts/{post_id}", response_model=schemas.PostViewModel) # <-- 1. CHANGE THIS URL
def track_post_view(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_current_user)
):
    """Track a view for a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    
    # Build the query to check for an existing view
    query = db.query(PostView).filter(
        PostView.post_id == post_id,
        PostView.viewed_at > one_hour_ago
    )

    if current_user:
        query = query.filter(PostView.user_id == current_user.id)
    else:
        query = query.filter(PostView.ip_address == client_ip)

    existing_view = query.first()
    
    # This entire block can be simplified as well, but we'll focus on the main fix.
    if not existing_view:
        view = PostView(
            post_id=post_id,
            user_id=current_user.id if current_user else None,
            ip_address=client_ip if not current_user else None,
            user_agent=user_agent
        )
        db.add(view)
        
        # --- 2. (Optional but Recommended) MAKE THIS MORE ROBUST ---
        post.view_count = (post.view_count or 0) + 1
        
        db.commit()
        db.refresh(post)
    
    # To avoid returning the entire post object, we can return a simple view model
    # This matches the response_model=schemas.PostViewModel
    final_view = db.query(PostView).filter(PostView.post_id == post_id).order_by(PostView.viewed_at.desc()).first()
    return final_view

@router.get("/posts/{post_id}/views", response_model=List[schemas.PostViewModel])
def get_post_views(
    post_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get view history for a post (admin only)."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    views = db.query(PostView).filter(PostView.post_id == post_id).order_by(
        PostView.viewed_at.desc()
    ).offset(skip).limit(limit).all()
    
    return views

@router.get("/posts/{post_id}/view-stats", response_model=schemas.PostViewStats)
def get_post_view_stats(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get view statistics for a post."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    now = datetime.datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - datetime.timedelta(days=7)
    month_ago = now - datetime.timedelta(days=30)
    
    # Total views
    total_views = post.view_count
    
    # Unique views (count distinct users + IPs)
    unique_views = db.query(PostView).filter(PostView.post_id == post_id).distinct(
        PostView.user_id, PostView.ip_address
    ).count()
    
    # Views today
    views_today = db.query(PostView).filter(
        PostView.post_id == post_id,
        PostView.viewed_at >= today
    ).count()
    
    # Views this week
    views_this_week = db.query(PostView).filter(
        PostView.post_id == post_id,
        PostView.viewed_at >= week_ago
    ).count()
    
    # Views this month
    views_this_month = db.query(PostView).filter(
        PostView.post_id == post_id,
        PostView.viewed_at >= month_ago
    ).count()
    
    return schemas.PostViewStats(
        total_views=total_views,
        unique_views=unique_views,
        views_today=views_today,
        views_this_week=views_this_week,
        views_this_month=views_this_month
    )

@router.get("/posts/popular", response_model=List[schemas.PostModel])
def get_popular_posts(
    skip: int = 0,
    limit: int = 20,
    timeframe: str = "all",  # "today", "week", "month", "all"
    db: Session = Depends(get_db)
):
    """Get most popular posts by view count."""
    now = datetime.datetime.utcnow()
    
    if timeframe == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == "week":
        start_date = now - datetime.timedelta(days=7)
    elif timeframe == "month":
        start_date = now - datetime.timedelta(days=30)
    else:  # "all"
        start_date = None
    
    query = db.query(Post).filter(Post.status == "public")
    
    if start_date:
        # Get posts with views in the specified timeframe
        posts_with_views = db.query(PostView.post_id).filter(
            PostView.viewed_at >= start_date
        ).subquery()
        query = query.join(posts_with_views, Post.id == posts_with_views.c.post_id)
    
    posts = query.order_by(Post.view_count.desc()).offset(skip).limit(limit).all()
    return posts

@router.get("/analytics/overview")
def get_analytics_overview(
    db: Session = Depends(get_db)
):
    """Get overall analytics overview."""
    now = datetime.datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - datetime.timedelta(days=7)
    month_ago = now - datetime.timedelta(days=30)
    
    # Total posts
    total_posts = db.query(Post).count()
    
    # Total views
    total_views = db.query(func.sum(Post.view_count)).scalar() or 0
    
    # Views today
    views_today = db.query(PostView).filter(PostView.viewed_at >= today).count()
    
    # Views this week
    views_this_week = db.query(PostView).filter(PostView.viewed_at >= week_ago).count()
    
    # Views this month
    views_this_month = db.query(PostView).filter(PostView.viewed_at >= month_ago).count()
    
    # Most popular post
    most_popular = db.query(Post).filter(Post.status == "public").order_by(
        Post.view_count.desc()
    ).first()
    
    return {
        "total_posts": total_posts,
        "total_views": total_views,
        "views_today": views_today,
        "views_this_week": views_this_week,
        "views_this_month": views_this_month,
        "most_popular_post": {
            "id": most_popular.id,
            "title": most_popular.title,
            "view_count": most_popular.view_count
        } if most_popular else None
    }
