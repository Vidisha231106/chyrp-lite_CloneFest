# routers/mathjax.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import re

from dependencies import get_db, get_current_user
from models import Post, User
import schemas

router = APIRouter(
    tags=["MathJax"],
)

class MathJaxService:
    """MathJax service for mathematical notation rendering."""
    
    MATH_PATTERNS = {
        'inline': r'\$([^$]+)\$',
        'display': r'\$\$([^$]+)\$\$',
        'latex': r'\\begin\{([^}]+)\}(.*?)\\end\{\1\}',
        'brackets': r'\\\[(.*?)\\\]',
        'parentheses': r'\\\((.*?)\\\)'
    }
    
    @staticmethod
    def detect_math_content(text: str) -> List[Dict[str, any]]:
        """Detect mathematical content in text."""
        if not text:
            return []
        
        math_expressions = []
        
        # Detect inline math
        inline_matches = re.finditer(MathJaxService.MATH_PATTERNS['inline'], text)
        for match in inline_matches:
            math_expressions.append({
                'type': 'inline',
                'expression': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'raw': match.group(0)
            })
        
        # Detect display math
        display_matches = re.finditer(MathJaxService.MATH_PATTERNS['display'], text)
        for match in display_matches:
            math_expressions.append({
                'type': 'display',
                'expression': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'raw': match.group(0)
            })
        
        # Detect LaTeX environments
        latex_matches = re.finditer(MathJaxService.MATH_PATTERNS['latex'], text, re.DOTALL)
        for match in latex_matches:
            math_expressions.append({
                'type': 'latex',
                'environment': match.group(1),
                'expression': match.group(2),
                'start': match.start(),
                'end': match.end(),
                'raw': match.group(0)
            })
        
        # Detect bracket math
        bracket_matches = re.finditer(MathJaxService.MATH_PATTERNS['brackets'], text)
        for match in bracket_matches:
            math_expressions.append({
                'type': 'display',
                'expression': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'raw': match.group(0)
            })
        
        # Detect parentheses math
        paren_matches = re.finditer(MathJaxService.MATH_PATTERNS['parentheses'], text)
        for match in paren_matches:
            math_expressions.append({
                'type': 'inline',
                'expression': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'raw': match.group(0)
            })
        
        return math_expressions
    
    @staticmethod
    def generate_mathjax_html(expression: str, math_type: str = 'inline') -> str:
        """Generate HTML for MathJax rendering."""
        if math_type == 'inline':
            return f'<span class="math-inline">\\({expression}\\)</span>'
        elif math_type == 'display':
            return f'<div class="math-display">\\[{expression}\\]</div>'
        elif math_type == 'latex':
            return f'<div class="math-latex">\\begin{{{expression.split('}')[0]}}}{expression.split('}')[1]}\\end{{{expression.split('}')[0]}}}</div>'
        else:
            return f'<span class="math-inline">\\({expression}\\)</span>'
    
    @staticmethod
    def process_post_content(post: Post) -> Dict[str, any]:
        """Process post content and convert math expressions to MathJax HTML."""
        if not post.body:
            return {
                "post_id": post.id,
                "original_content": post.body,
                "processed_content": post.body,
                "math_expressions": []
            }
        
        math_expressions = MathJaxService.detect_math_content(post.body)
        processed_content = post.body
        
        # Replace math expressions with HTML (in reverse order to maintain positions)
        for math_expr in reversed(math_expressions):
            html = MathJaxService.generate_mathjax_html(
                math_expr['expression'], 
                math_expr['type']
            )
            processed_content = (
                processed_content[:math_expr['start']] + 
                html + 
                processed_content[math_expr['end']:]
            )
        
        return {
            "post_id": post.id,
            "original_content": post.body,
            "processed_content": processed_content,
            "math_expressions": math_expressions
        }
    
    @staticmethod
    def validate_math_expression(expression: str) -> Dict[str, any]:
        """Validate a mathematical expression."""
        if not expression.strip():
            return {
                "valid": False,
                "message": "Expression cannot be empty"
            }
        
        # Basic validation - check for common LaTeX syntax
        common_patterns = [
            r'\\[a-zA-Z]+',  # LaTeX commands
            r'\{[^}]*\}',    # Braces
            r'\[[^\]]*\]',   # Square brackets
            r'\([^)]*\)',    # Parentheses
            r'[a-zA-Z0-9+\-*/=<>]',  # Basic math symbols
            r'\\[a-zA-Z]+',  # Greek letters and symbols
        ]
        
        has_valid_syntax = any(re.search(pattern, expression) for pattern in common_patterns)
        
        return {
            "valid": has_valid_syntax,
            "expression": expression,
            "message": "Valid mathematical expression" if has_valid_syntax else "Invalid mathematical expression"
        }
    
    @staticmethod
    def get_mathjax_config() -> Dict[str, any]:
        """Get MathJax configuration."""
        return {
            "config": {
                "tex": {
                    "inlineMath": [["\\(", "\\)"]],
                    "displayMath": [["\\[", "\\]"]],
                    "processEscapes": True,
                    "processEnvironments": True
                },
                "options": {
                    "skipHtmlTags": ["script", "noscript", "style", "textarea", "pre"]
                }
            },
            "src": "https://polyfill.io/v3/polyfill.min.js?features=es6",
            "mathjax": "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        }

@router.post("/mathjax/process", tags=["MathJax"])
def process_content_for_math(
    content: str,
    current_user: User = Depends(get_current_user)
):
    """Process content and convert math expressions to MathJax HTML."""
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    math_expressions = MathJaxService.detect_math_content(content)
    processed_content = content
    
    # Replace math expressions with HTML
    for math_expr in reversed(math_expressions):
        html = MathJaxService.generate_mathjax_html(
            math_expr['expression'], 
            math_expr['type']
        )
        processed_content = (
            processed_content[:math_expr['start']] + 
            html + 
            processed_content[math_expr['end']:]
        )
    
    return {
        "original_content": content,
        "processed_content": processed_content,
        "math_expressions": math_expressions,
        "total_expressions": len(math_expressions)
    }

@router.get("/mathjax/post/{post_id}/processed", tags=["MathJax"])
def get_post_with_math(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get a post with mathematical content processed."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return MathJaxService.process_post_content(post)

@router.post("/mathjax/validate", tags=["MathJax"])
def validate_math_expression(
    expression: str,
    current_user: User = Depends(get_current_user)
):
    """Validate a mathematical expression."""
    if not expression.strip():
        raise HTTPException(status_code=400, detail="Expression cannot be empty")
    
    return MathJaxService.validate_math_expression(expression)

@router.get("/mathjax/config", tags=["MathJax"])
def get_mathjax_configuration():
    """Get MathJax configuration for frontend."""
    return MathJaxService.get_mathjax_config()

@router.post("/mathjax/preview", tags=["MathJax"])
def preview_math_expression(
    expression: str,
    math_type: str = "inline",
    current_user: User = Depends(get_current_user)
):
    """Preview how a mathematical expression will be rendered."""
    if not expression.strip():
        raise HTTPException(status_code=400, detail="Expression cannot be empty")
    
    if math_type not in ['inline', 'display', 'latex']:
        raise HTTPException(status_code=400, detail="Invalid math type")
    
    html = MathJaxService.generate_mathjax_html(expression, math_type)
    
    return {
        "expression": expression,
        "math_type": math_type,
        "html": html,
        "preview": True
    }

@router.get("/mathjax/examples", tags=["MathJax"])
def get_math_examples():
    """Get examples of mathematical expressions."""
    return {
        "examples": [
            {
                "type": "inline",
                "expression": "E = mc^2",
                "description": "Einstein's mass-energy equivalence"
            },
            {
                "type": "display",
                "expression": "\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}",
                "description": "Gaussian integral"
            },
            {
                "type": "latex",
                "expression": "\\begin{matrix} a & b \\\\ c & d \\end{matrix}",
                "description": "Matrix"
            },
            {
                "type": "inline",
                "expression": "\\frac{a}{b}",
                "description": "Fraction"
            },
            {
                "type": "display",
                "expression": "\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}",
                "description": "Basel problem"
            }
        ]
    }
