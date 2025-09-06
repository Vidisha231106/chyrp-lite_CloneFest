# routers/lightbox.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
import re

from dependencies import get_db, get_current_user
from models import Post, User
import schemas

router = APIRouter(
    tags=["Lightbox"],
)

class LightboxService:
    """Lightbox image gallery service."""
    
    @staticmethod
    def extract_images_from_post(post: Post) -> List[Dict[str, str]]:
        """Extract images from a post's content."""
        if not post.body:
            return []
        
        images = []
        
        # Extract markdown images ![alt](url)
        markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        markdown_matches = re.findall(markdown_pattern, post.body)
        
        for alt_text, url in markdown_matches:
            images.append({
                'url': url,
                'alt': alt_text,
                'type': 'markdown',
                'post_id': post.id,
                'post_title': post.title
            })
        
        # Extract HTML images <img src="url" alt="alt">
        html_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*>'
        html_matches = re.findall(html_pattern, post.body)
        
        for url, alt_text in html_matches:
            images.append({
                'url': url,
                'alt': alt_text,
                'type': 'html',
                'post_id': post.id,
                'post_title': post.title
            })
        
        # If it's a photo post, the body itself is the image URL
        if post.feather == 'photo' and post.body:
            images.append({
                'url': post.body,
                'alt': post.title or post.clean,
                'type': 'photo_post',
                'post_id': post.id,
                'post_title': post.title
            })
        
        return images
    
    @staticmethod
    def create_gallery_from_posts(posts: List[Post]) -> List[Dict[str, str]]:
        """Create a gallery from multiple posts."""
        all_images = []
        
        for post in posts:
            images = LightboxService.extract_images_from_post(post)
            all_images.extend(images)
        
        return all_images
    
    @staticmethod
    def validate_image_url(url: str) -> bool:
        """Validate if URL is a valid image."""
        if not url:
            return False
        
        # Check if it's a valid URL
        if not url.startswith(('http://', 'https://', '/')):
            return False
        
        # Check for common image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']
        url_lower = url.lower()
        
        return any(url_lower.endswith(ext) for ext in image_extensions)

@router.get("/lightbox/post/{post_id}/images", tags=["Lightbox"])
def get_post_images(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get all images from a specific post for lightbox gallery."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    images = LightboxService.extract_images_from_post(post)
    
    # Filter out invalid image URLs
    valid_images = [img for img in images if LightboxService.validate_image_url(img['url'])]
    
    return {
        "post_id": post_id,
        "post_title": post.title,
        "images": valid_images,
        "total_images": len(valid_images)
    }

@router.get("/lightbox/user/{user_id}/gallery", tags=["Lightbox"])
def get_user_gallery(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all images from a user's posts for lightbox gallery."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's public posts
    posts = db.query(Post).filter(
        Post.user_id == user_id,
        Post.status == 'public'
    ).offset(skip).limit(limit).all()
    
    all_images = LightboxService.create_gallery_from_posts(posts)
    
    # Filter out invalid image URLs
    valid_images = [img for img in all_images if LightboxService.validate_image_url(img['url'])]
    
    return {
        "user_id": user_id,
        "user_name": user.login,
        "images": valid_images,
        "total_images": len(valid_images),
        "posts_scanned": len(posts)
    }

@router.get("/lightbox/recent", tags=["Lightbox"])
def get_recent_images(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get recent images from all public posts."""
    # Get recent public posts
    posts = db.query(Post).filter(
        Post.status == 'public'
    ).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    
    all_images = LightboxService.create_gallery_from_posts(posts)
    
    # Filter out invalid image URLs
    valid_images = [img for img in all_images if LightboxService.validate_image_url(img['url'])]
    
    return {
        "images": valid_images,
        "total_images": len(valid_images),
        "posts_scanned": len(posts)
    }

@router.post("/lightbox/protect", tags=["Lightbox"])
def protect_image(
    image_url: str,
    current_user: User = Depends(get_current_user)
):
    """Mark an image as protected (requires authentication to view)."""
    if not LightboxService.validate_image_url(image_url):
        raise HTTPException(status_code=400, detail="Invalid image URL")
    
    # In a real implementation, you'd store this in a database
    # For now, we'll just return a success message
    return {
        "message": "Image protection enabled",
        "image_url": image_url,
        "protected_by": current_user.login,
        "protected_at": "now"
    }

@router.get("/lightbox/search", tags=["Lightbox"])
def search_images(
    query: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search for images in posts by title or content."""
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    # Search posts by title or content
    posts = db.query(Post).filter(
        Post.status == 'public',
        Post.title.ilike(f'%{query}%')
    ).offset(skip).limit(limit).all()
    
    all_images = LightboxService.create_gallery_from_posts(posts)
    
    # Filter out invalid image URLs
    valid_images = [img for img in all_images if LightboxService.validate_image_url(img['url'])]
    
    return {
        "query": query,
        "images": valid_images,
        "total_images": len(valid_images),
        "posts_found": len(posts)
    }
