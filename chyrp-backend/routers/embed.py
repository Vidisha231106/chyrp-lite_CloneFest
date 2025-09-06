# routers/embed.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import re
from urllib.parse import urlparse
import requests

from dependencies import get_db, get_current_user
from models import Post, User
from utils import detect_embed_urls
import schemas

router = APIRouter(
    tags=["Easy Embed"],
)

class EmbedService:
    """Easy embed service for external content."""
    
    EMBED_PATTERNS = {
        'youtube': [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)'
        ],
        'twitter': [
            r'https?://(?:www\.)?twitter\.com/\w+/status/(\d+)',
            r'https?://(?:www\.)?x\.com/\w+/status/(\d+)'
        ],
        'instagram': [
            r'https?://(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?instagram\.com/reel/([a-zA-Z0-9_-]+)'
        ],
        'vimeo': [
            r'https?://(?:www\.)?vimeo\.com/(\d+)'
        ],
        'codepen': [
            r'https?://(?:www\.)?codepen\.io/\w+/pen/([a-zA-Z0-9_-]+)'
        ],
        'github': [
            r'https?://(?:www\.)?github\.com/([^/]+)/([^/]+)'
        ],
        'gist': [
            r'https?://(?:www\.)?gist\.github\.com/([^/]+)/([a-zA-Z0-9_-]+)'
        ]
    }
    
    @staticmethod
    def detect_embeds(text: str) -> List[Dict[str, str]]:
        """Detect embeddable URLs in text."""
        if not text:
            return []
        
        embeds = []
        
        for platform, patterns in EmbedService.EMBED_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    embeds.append({
                        'platform': platform,
                        'url': match.group(0),
                        'id': match.group(1) if match.groups() else None,
                        'start': match.start(),
                        'end': match.end()
                    })
        
        return embeds
    
    @staticmethod
    def generate_embed_html(platform: str, url: str, embed_id: str = None) -> str:
        """Generate HTML for embedded content."""
        if platform == 'youtube':
            video_id = embed_id or url.split('v=')[1].split('&')[0] if 'v=' in url else url.split('/')[-1]
            return f'<div class="embed-container"><iframe src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe></div>'
        
        elif platform == 'twitter':
            tweet_id = embed_id or url.split('/')[-1]
            return f'<div class="embed-container"><blockquote class="twitter-tweet" data-theme="light"><a href="{url}"></a></blockquote><script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script></div>'
        
        elif platform == 'instagram':
            post_id = embed_id or url.split('/')[-1]
            return f'<div class="embed-container"><blockquote class="instagram-media" data-instgrm-permalink="{url}" data-instgrm-version="14"></blockquote><script async src="//www.instagram.com/embed.js"></script></div>'
        
        elif platform == 'vimeo':
            video_id = embed_id or url.split('/')[-1]
            return f'<div class="embed-container"><iframe src="https://player.vimeo.com/video/{video_id}" frameborder="0" allowfullscreen></iframe></div>'
        
        elif platform == 'codepen':
            pen_id = embed_id or url.split('/')[-1]
            return f'<div class="embed-container"><iframe src="https://codepen.io/embed/{pen_id}" frameborder="0" allowfullscreen></iframe></div>'
        
        elif platform == 'github':
            return f'<div class="embed-container"><iframe src="https://github.com/{embed_id}" frameborder="0" allowfullscreen></iframe></div>'
        
        elif platform == 'gist':
            return f'<div class="embed-container"><script src="https://gist.github.com/{embed_id}.js"></script></div>'
        
        else:
            return f'<div class="embed-container"><a href="{url}" target="_blank" rel="noopener">{url}</a></div>'
    
    @staticmethod
    def process_post_content(post: Post) -> Dict[str, any]:
        """Process post content and convert URLs to embeds."""
        if not post.body:
            return {
                "post_id": post.id,
                "original_content": post.body,
                "processed_content": post.body,
                "embeds": []
            }
        
        embeds = EmbedService.detect_embeds(post.body)
        processed_content = post.body
        
        # Replace URLs with embed HTML (in reverse order to maintain positions)
        for embed in reversed(embeds):
            embed_html = EmbedService.generate_embed_html(
                embed['platform'], 
                embed['url'], 
                embed['id']
            )
            processed_content = (
                processed_content[:embed['start']] + 
                embed_html + 
                processed_content[embed['end']:]
            )
        
        return {
            "post_id": post.id,
            "original_content": post.body,
            "processed_content": processed_content,
            "embeds": embeds
        }
    
    @staticmethod
    def validate_embed_url(url: str) -> bool:
        """Validate if URL can be embedded."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check against known embed patterns
            for platform, patterns in EmbedService.EMBED_PATTERNS.items():
                for pattern in patterns:
                    if re.match(pattern, url):
                        return True
            
            return False
        except:
            return False

@router.post("/embed/process", tags=["Easy Embed"])
def process_content_for_embeds(
    content: str,
    current_user: User = Depends(get_current_user)
):
    """Process content and convert URLs to embeds."""
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    embeds = EmbedService.detect_embeds(content)
    processed_content = content
    
    # Replace URLs with embed HTML
    for embed in reversed(embeds):
        embed_html = EmbedService.generate_embed_html(
            embed['platform'], 
            embed['url'], 
            embed['id']
        )
        processed_content = (
            processed_content[:embed['start']] + 
            embed_html + 
            processed_content[embed['end']:]
        )
    
    return {
        "original_content": content,
        "processed_content": processed_content,
        "embeds": embeds,
        "total_embeds": len(embeds)
    }

@router.get("/embed/post/{post_id}/processed", tags=["Easy Embed"])
def get_post_with_embeds(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get a post with embedded content processed."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return EmbedService.process_post_content(post)

@router.post("/embed/validate", tags=["Easy Embed"])
def validate_embed_url(
    url: str,
    current_user: User = Depends(get_current_user)
):
    """Validate if a URL can be embedded."""
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    is_valid = EmbedService.validate_embed_url(url)
    embeds = EmbedService.detect_embeds(url)
    
    return {
        "url": url,
        "is_embeddable": is_valid,
        "platform": embeds[0]['platform'] if embeds else None,
        "embed_id": embeds[0]['id'] if embeds else None
    }

@router.get("/embed/platforms", tags=["Easy Embed"])
def get_supported_platforms():
    """Get list of supported embed platforms."""
    return {
        "platforms": list(EmbedService.EMBED_PATTERNS.keys()),
        "patterns": EmbedService.EMBED_PATTERNS
    }

@router.post("/embed/preview", tags=["Easy Embed"])
def preview_embed(
    url: str,
    current_user: User = Depends(get_current_user)
):
    """Preview how a URL will be embedded."""
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    embeds = EmbedService.detect_embeds(url)
    if not embeds:
        raise HTTPException(status_code=400, detail="URL is not embeddable")
    
    embed = embeds[0]
    embed_html = EmbedService.generate_embed_html(
        embed['platform'], 
        embed['url'], 
        embed['id']
    )
    
    return {
        "url": url,
        "platform": embed['platform'],
        "embed_id": embed['id'],
        "embed_html": embed_html,
        "preview": True
    }
