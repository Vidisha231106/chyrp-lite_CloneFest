# routers/maptcha.py

import random
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict

from dependencies import get_db, get_current_user
from dependencies import get_db
from models import Comment, Post, User
import schemas

router = APIRouter(
    tags=["MAPTCHA"],
)

class MAPTCHAService:
    """Math-based CAPTCHA service."""
    
    @staticmethod
    def generate_challenge() -> Dict[str, str]:
        """Generate a math challenge."""
        operations = ['+', '-', '*']
        operation = random.choice(operations)
        
        if operation == '+':
            a = random.randint(1, 50)
            b = random.randint(1, 50)
            answer = a + b
            question = f"{a} + {b}"
        elif operation == '-':
            a = random.randint(20, 100)
            b = random.randint(1, a)
            answer = a - b
            question = f"{a} - {b}"
        else:  # multiplication
            a = random.randint(2, 12)
            b = random.randint(2, 12)
            answer = a * b
            question = f"{a} × {b}"
        
        # Create a hash of the answer for verification
        answer_hash = hashlib.md5(str(answer).encode()).hexdigest()
        
        return {
            "question": question,
            "challenge_id": answer_hash,
            "difficulty": "easy"
        }
    
# routers/maptcha.py

    @staticmethod
    def verify_answer(challenge_id: str, user_answer: str) -> bool:
        """Verify the user's answer by hashing it and comparing to the challenge ID."""
        try:
            # Hash the user's answer using the same method as generation
            user_answer_hash = hashlib.md5(user_answer.strip().encode()).hexdigest()
            
            # Compare the generated hash with the challenge_id from the frontend
            return user_answer_hash == challenge_id
        except Exception:
            # If any error occurs (e.g., non-numeric input), fail verification
            return False

@router.post("/maptcha/generate", tags=["MAPTCHA"])
def generate_maptcha():
    """Generate a new MAPTCHA challenge."""
    return MAPTCHAService.generate_challenge()

@router.post("/maptcha/verify", tags=["MAPTCHA"])
def verify_maptcha(
    challenge_id: str,
    answer: str,
    db: Session = Depends(get_db)
):
    """Verify a MAPTCHA answer."""
    is_valid = MAPTCHAService.verify_answer(challenge_id, answer)
    
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail="Incorrect answer. Please try again."
        )
    
    return {"verified": True, "message": "MAPTCHA verified successfully"}

@router.post("/posts/{post_id}/comments/with-maptcha", response_model=schemas.CommentModel, tags=["Comments"])
def create_comment_with_maptcha(
    post_id: int,
    data: schemas.CommentCreateWithMaptcha, # <-- Use the new unified schema
    db: Session = Depends(get_db),
    # This endpoint should probably not require a logged-in user if it has a CAPTCHA,
    # but we'll leave it for now to match the original code.
    current_user: User = Depends(get_current_user) 
):
    """Create a comment with MAPTCHA verification."""
    # Verify MAPTCHA first using data from the new schema
    is_valid = MAPTCHAService.verify_answer(data.maptcha_challenge_id, data.maptcha_answer)
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail="MAPTCHA verification failed. Please check your answer to the math question."
        )
    
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if data.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == data.parent_id).first()
        if not parent_comment or parent_comment.post_id != post_id:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    db_comment = Comment(
        content=data.content,
        post_id=post_id,
        user_id=current_user.id,
        parent_id=data.parent_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment
