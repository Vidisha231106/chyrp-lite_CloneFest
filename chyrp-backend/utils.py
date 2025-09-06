# utils.py

import re
from typing import Optional

def generate_excerpt(text: str, max_length: int = 200) -> str:
    """Generate an excerpt from text content."""
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'#+\s*', '', text)  # Remove headers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # Remove italic
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Remove links
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)  # Remove images
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Remove code blocks
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Truncate if too long
    if len(text) <= max_length:
        return text
    
    # Find the last complete word
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can find a good break point
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."

def extract_code_blocks(text: str) -> list:
    """Extract code blocks from markdown text."""
    if not text:
        return []
    
    # Find code blocks with language specification
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            'language': language or 'text',
            'code': code.strip()
        })
    
    return code_blocks

def detect_embed_urls(text: str) -> list:
    """Detect URLs that can be embedded."""
    if not text:
        return []
    
    # Common embeddable platforms
    embed_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'https?://(?:www\.)?twitter\.com/\w+/status/(\d+)',
        r'https?://(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)',
        r'https?://(?:www\.)?vimeo\.com/(\d+)',
        r'https?://(?:www\.)?codepen\.io/\w+/pen/([a-zA-Z0-9_-]+)',
    ]
    
    embed_urls = []
    for pattern in embed_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            embed_urls.append({
                'platform': pattern.split('/')[2].split('.')[0],
                'id': match,
                'url': text[text.find(match):text.find(match) + len(match) + 20]
            })
    
    return embed_urls

def create_slug(name: str) -> str:
    """Create a URL-friendly slug from a name."""
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^a-z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug