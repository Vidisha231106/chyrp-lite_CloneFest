# routers/mentionable.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin
import re
from datetime import datetime
import requests

from dependencies import get_db, get_current_user
from models import Post, User
import schemas

router = APIRouter(
    tags=["Mentionable"],
)

class WebmentionService:
    """Webmention service for receiving and processing mentions."""
    
    @staticmethod
    def extract_links_from_content(content: str) -> List[str]:
        """Extract all links from content."""
        if not content:
            return []
        
        # Find all URLs in the content
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)
        
        return urls
    
    @staticmethod
    def discover_webmention_endpoint(url: str) -> Optional[str]:
        """Discover webmention endpoint for a URL."""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Chyrp-Lite-Webmention-Bot/1.0'
            })
            
            # Check Link header
            link_header = response.headers.get('Link', '')
            webmention_match = re.search(r'<([^>]+)>;\s*rel=["\']?webmention["\']?', link_header)
            if webmention_match:
                return webmention_match.group(1)
            
            # Check HTML for webmention link
            html_content = response.text
            webmention_pattern = r'<link[^>]+rel=["\']?webmention["\']?[^>]+href=["\']([^"\']+)["\']'
            webmention_match = re.search(webmention_pattern, html_content)
            if webmention_match:
                return webmention_match.group(1)
            
            return None
        except:
            return None
    
    @staticmethod
    def send_webmention(source_url: str, target_url: str) -> Dict[str, any]:
        """Send a webmention to a target URL."""
        endpoint = WebmentionService.discover_webmention_endpoint(target_url)
        
        if not endpoint:
            return {
                "success": False,
                "message": "No webmention endpoint found",
                "target_url": target_url
            }
        
        try:
            response = requests.post(endpoint, data={
                'source': source_url,
                'target': target_url
            }, timeout=30)
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "message": response.text,
                "target_url": target_url,
                "endpoint": endpoint
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "target_url": target_url,
                "endpoint": endpoint
            }
    
    @staticmethod
    def process_incoming_webmention(source_url: str, target_url: str, db: Session) -> Dict[str, any]:
        """Process an incoming webmention."""
        try:
            # Fetch source content
            response = requests.get(source_url, timeout=10, headers={
                'User-Agent': 'Chyrp-Lite-Webmention-Bot/1.0'
            })
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": "Could not fetch source content",
                    "source_url": source_url
                }
            
            html_content = response.text
            
            # Extract metadata
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1) if title_match else "Untitled"
            
            # Extract author information
            author_match = re.search(r'<meta[^>]+name=["\']author["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            author = author_match.group(1) if author_match else "Unknown"
            
            # Extract description
            desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            description = desc_match.group(1) if desc_match else ""
            
            # Find the target post
            target_post = db.query(Post).filter(Post.clean == target_url.split('/')[-1]).first()
            if not target_post:
                return {
                    "success": False,
                    "message": "Target post not found",
                    "target_url": target_url
                }
            
            # Store webmention (in a real implementation, you'd have a Webmention model)
            webmention_data = {
                "source_url": source_url,
                "target_url": target_url,
                "target_post_id": target_post.id,
                "source_title": title,
                "source_author": author,
                "source_description": description,
                "received_at": datetime.utcnow(),
                "status": "approved"
            }
            
            return {
                "success": True,
                "message": "Webmention processed successfully",
                "webmention": webmention_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "source_url": source_url
            }

@router.post("/webmention/receive", tags=["Mentionable"])
def receive_webmention(
    source: str,
    target: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Receive a webmention."""
    if not source or not target:
        raise HTTPException(status_code=400, detail="Source and target URLs are required")
    
    result = WebmentionService.process_incoming_webmention(source, target, db)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["message"])

@router.post("/webmention/send", tags=["Mentionable"])
def send_webmention(
    source_url: str,
    target_url: str,
    current_user: User = Depends(get_current_user)
):
    """Send a webmention to a target URL."""
    if not source_url or not target_url:
        raise HTTPException(status_code=400, detail="Source and target URLs are required")
    
    result = WebmentionService.send_webmention(source_url, target_url)
    return result

@router.post("/webmention/discover", tags=["Mentionable"])
def discover_webmention_endpoint(
    url: str,
    current_user: User = Depends(get_current_user)
):
    """Discover webmention endpoint for a URL."""
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    
    endpoint = WebmentionService.discover_webmention_endpoint(url)
    
    return {
        "url": url,
        "webmention_endpoint": endpoint,
        "has_endpoint": endpoint is not None
    }

@router.get("/webmention/endpoint", tags=["Mentionable"])
def get_webmention_endpoint():
    """Get the webmention endpoint for this site."""
    return {
        "webmention_endpoint": "/webmention/receive",
        "message": "Send webmentions to this endpoint"
    }

@router.post("/webmention/process-post", tags=["Mentionable"])
def process_post_for_webmentions(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process a post and send webmentions for all links."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if not post.body:
        return {
            "post_id": post_id,
            "message": "No content to process",
            "webmentions_sent": 0
        }
    
    # Extract links from post content
    links = WebmentionService.extract_links_from_content(post.body)
    
    # Send webmentions
    results = []
    for link in links:
        result = WebmentionService.send_webmention(
            f"https://yoursite.com/posts/{post.clean}",  # Replace with actual site URL
            link
        )
        results.append(result)
    
    successful = sum(1 for r in results if r["success"])
    
    return {
        "post_id": post_id,
        "links_found": len(links),
        "webmentions_sent": successful,
        "results": results
    }

@router.get("/webmention/pingback", tags=["Mentionable"])
def pingback_endpoint():
    """Pingback endpoint (simplified webmention alternative)."""
    return {
        "message": "Pingback endpoint",
        "note": "This is a simplified pingback endpoint. Use webmention/receive for full webmention support."
    }
