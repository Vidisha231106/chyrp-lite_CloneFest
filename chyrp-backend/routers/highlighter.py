# routers/highlighter.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
import re

from dependencies import get_db
from models import Post
from utils import extract_code_blocks
import schemas

router = APIRouter(
    tags=["Highlighter"],
)

class SyntaxHighlighter:
    """Syntax highlighting service."""
    
    # Common programming languages and their extensions
    LANGUAGE_MAP = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'html': 'html',
        'css': 'css',
        'scss': 'scss',
        'json': 'json',
        'xml': 'xml',
        'sql': 'sql',
        'bash': 'bash',
        'sh': 'bash',
        'yaml': 'yaml',
        'yml': 'yaml',
        'md': 'markdown',
        'go': 'go',
        'rs': 'rust',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'php': 'php',
        'rb': 'ruby',
        'swift': 'swift',
        'kt': 'kotlin',
        'dart': 'dart',
        'vue': 'vue',
        'jsx': 'jsx',
        'tsx': 'tsx',
    }
    
    @staticmethod
    def detect_language(code: str, hint: str = None) -> str:
        """Detect programming language from code or hint."""
        if hint and hint.lower() in SyntaxHighlighter.LANGUAGE_MAP:
            return SyntaxHighlighter.LANGUAGE_MAP[hint.lower()]
        
        # Simple heuristics for language detection
        code_lower = code.lower().strip()
        
        if code_lower.startswith('<!doctype') or '<html' in code_lower:
            return 'html'
        elif code_lower.startswith('import ') and 'from ' in code_lower:
            return 'python'
        elif code_lower.startswith('function ') or 'const ' in code_lower or 'let ' in code_lower:
            return 'javascript'
        elif code_lower.startswith('SELECT ') or 'FROM ' in code_lower:
            return 'sql'
        elif code_lower.startswith('#!/bin/bash') or 'echo ' in code_lower:
            return 'bash'
        elif code_lower.startswith('package ') and 'import ' in code_lower:
            return 'go'
        elif code_lower.startswith('fn ') or 'let ' in code_lower and 'mut ' in code_lower:
            return 'rust'
        else:
            return 'text'
    
    @staticmethod
    def highlight_code(code: str, language: str = None) -> Dict[str, str]:
        """Highlight code with syntax highlighting."""
        if not language:
            language = SyntaxHighlighter.detect_language(code)
        
        # This is a simplified version - in production, use a proper syntax highlighter
        # like Pygments or highlight.js
        highlighted_code = code
        
        # Basic syntax highlighting patterns
        if language == 'python':
            highlighted_code = SyntaxHighlighter._highlight_python(code)
        elif language == 'javascript':
            highlighted_code = SyntaxHighlighter._highlight_javascript(code)
        elif language == 'html':
            highlighted_code = SyntaxHighlighter._highlight_html(code)
        elif language == 'css':
            highlighted_code = SyntaxHighlighter._highlight_css(code)
        
        return {
            'language': language,
            'code': highlighted_code,
            'raw_code': code
        }
    
    @staticmethod
    def _highlight_python(code: str) -> str:
        """Basic Python syntax highlighting."""
        # Keywords
        keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span class="keyword">{keyword}</span>', code)
        
        # Strings
        code = re.sub(r'("[^"]*")', r'<span class="string">\1</span>', code)
        code = re.sub(r"('[^']*')", r'<span class="string">\1</span>', code)
        
        # Comments
        code = re.sub(r'(#.*)$', r'<span class="comment">\1</span>', code, flags=re.MULTILINE)
        
        return code
    
    @staticmethod
    def _highlight_javascript(code: str) -> str:
        """Basic JavaScript syntax highlighting."""
        keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'return', 'class', 'import', 'export', 'async', 'await', 'try', 'catch', 'finally']
        for keyword in keywords:
            code = re.sub(rf'\b{keyword}\b', f'<span class="keyword">{keyword}</span>', code)
        
        # Strings
        code = re.sub(r'("[^"]*")', r'<span class="string">\1</span>', code)
        code = re.sub(r"('[^']*')", r'<span class="string">\1</span>', code)
        
        # Comments
        code = re.sub(r'(//.*)$', r'<span class="comment">\1</span>', code, flags=re.MULTILINE)
        code = re.sub(r'(/\*.*?\*/)', r'<span class="comment">\1</span>', code, flags=re.DOTALL)
        
        return code
    
    @staticmethod
    def _highlight_html(code: str) -> str:
        """Basic HTML syntax highlighting."""
        # Tags
        code = re.sub(r'<([^>]+)>', r'<span class="tag">&lt;\1&gt;</span>', code)
        
        # Attributes
        code = re.sub(r'(\w+)=', r'<span class="attr">\1</span>=', code)
        
        return code
    
    @staticmethod
    def _highlight_css(code: str) -> str:
        """Basic CSS syntax highlighting."""
        # Selectors
        code = re.sub(r'([.#]?\w+)\s*{', r'<span class="selector">\1</span> {', code)
        
        # Properties
        code = re.sub(r'(\w+):', r'<span class="property">\1</span>:', code)
        
        # Values
        code = re.sub(r':\s*([^;]+);', r': <span class="value">\1</span>;', code)
        
        return code

@router.post("/highlighter/analyze", tags=["Highlighter"])
def analyze_post_code(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Analyze a post for code blocks and return highlighted versions."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if not post.body:
        return {"code_blocks": []}
    
    # Extract code blocks
    code_blocks = extract_code_blocks(post.body)
    
    # Highlight each code block
    highlighted_blocks = []
    for block in code_blocks:
        highlighted = SyntaxHighlighter.highlight_code(block['code'], block['language'])
        highlighted_blocks.append(highlighted)
    
    return {
        "post_id": post_id,
        "code_blocks": highlighted_blocks,
        "total_blocks": len(highlighted_blocks)
    }

@router.post("/highlighter/highlight", tags=["Highlighter"])
def highlight_code_text(
    code: str,
    language: str = None
):
    """Highlight a code snippet."""
    if not code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    highlighted = SyntaxHighlighter.highlight_code(code, language)
    return highlighted

@router.get("/highlighter/languages", tags=["Highlighter"])
def get_supported_languages():
    """Get list of supported programming languages."""
    return {
        "languages": list(SyntaxHighlighter.LANGUAGE_MAP.values()),
        "extensions": SyntaxHighlighter.LANGUAGE_MAP
    }
