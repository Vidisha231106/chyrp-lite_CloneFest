# main.py

import base64
from io import BytesIO
import datetime
from typing import List, Optional, Dict
from supabase import Client, create_client
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Add upload-related imports
from fastapi import UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
import os, shutil
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
# --- Import from our custom files ---
import models
import schemas
from schemas import MediaModel  # Import MediaModel
from database import engine, SessionLocal
from dependencies import (
    get_db, 
    get_current_user, 
    create_access_token, 
    get_password_hash, 
    verify_password,
    require_permission,      
    require_post_permission  
)
from routers import interactions
import os
from dotenv import load_dotenv

load_dotenv() # Make sure environment variables are loaded from .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase URL and Key must be set in your .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# --- End Supabase Initialization ---

# ===============================================================================
# 1. FASTAPI APP INITIALIZATION & MIDDLEWARE
# ===============================================================================
app = FastAPI(
    title="Chyrp Clone API",
    description="API for the modern Chyrp blogging engine.",
    version="1.0.0",
)

async def upload_file_to_supabase(file: UploadFile, bucket_name: str, token: str) -> str:
    """Helper function to upload a file to a Supabase bucket and return its public URL."""
    
    # Set the authentication for the storage client for this specific request
    # This tells Supabase WHO is uploading the file.
    supabase.storage.set_auth(token)

    file_content = await file.read()
    file_path_in_bucket = f"public/{uuid4().hex}{os.path.splitext(file.filename)[1]}"

    # Now, the upload will be authenticated
    supabase.storage.from_(bucket_name).upload(
        path=file_path_in_bucket,
        file=file_content,
        file_options={"content-type": file.content_type}
    )
    
    return supabase.storage.from_(bucket_name).get_public_url(file_path_in_bucket)

# Directory to store uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve /uploads/<filename> as static files in dev
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers from other files ---
app.include_router(interactions.router)

# --- Create Database Tables on Startup ---
models.Base.metadata.create_all(bind=engine)

# File type validation
ALLOWED_MIME_TYPES = {
    'image': ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
    'audio': ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/aac'],
    'video': ['video/mp4', 'video/webm', 'video/avi', 'video/quicktime', 'video/x-msvideo']
}

MAX_FILE_SIZES = {
    'image': 10 * 1024 * 1024,    # 10MB
    'audio': 50 * 1024 * 1024,    # 50MB  
    'video': 100 * 1024 * 1024,   # 100MB
}

# ===============================================================================
# 2. STARTUP EVENT (DATABASE SEEDING)
# ===============================================================================
@app.on_event("startup")
def create_initial_data():
    db = SessionLocal()
    try:
        if db.query(models.Group).first() is None:
            print("Database is empty. Seeding initial data...")
            
            # Create Groups
            admin_permissions = ["edit_post", "delete_post", "add_user", "edit_user", "delete_user", "add_group", "edit_group", "delete_group", "like_post", "add_post", "edit_own_post", "delete_own_post"]
            member_permissions = ["add_post", "edit_own_post", "delete_own_post", "like_post"]
            admin_group = models.Group(name="Admin", permissions=admin_permissions)
            member_group = models.Group(name="Member", permissions=member_permissions)
            db.add(admin_group)
            db.add(member_group)
            db.commit()
            db.refresh(admin_group)
            
            # Create Admin User
            hashed_password = get_password_hash("admin")
            admin_user = models.User(login="admin", email="admin@example.com", full_name="Administrator", hashed_password=hashed_password, group_id=admin_group.id)
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            # Create Static Pages
            about_page = models.Post(content_type="page", title="About Us", body="## Welcome!\n\nThis is the default 'About Us' page.", clean="about-us", status="public", user_id=admin_user.id)
            contact_page = models.Post(content_type="page", title="Contact", body="This is the default 'Contact' page.", clean="contact", status="public", user_id=admin_user.id)
            db.add(about_page)
            db.add(contact_page)
            db.commit()
            print("Initial data created successfully.")
        else:
            print("Database already contains data. Skipping seeding.")
    finally:
        db.close()

def validate_file_upload(file: UploadFile, expected_type: str = None) -> Dict:
    """Validate uploaded file and return file info"""
    
    # Determine file category
    file_category = None
    for category, mime_types in ALLOWED_MIME_TYPES.items():
        if file.content_type in mime_types:
            file_category = category
            break
    
    if not file_category:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Check if specific type was expected
    if expected_type and file_category != expected_type:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {expected_type} file, got {file_category}"
        )
    
    return {
        'category': file_category,
        'mime_type': file.content_type,
        'max_size': MAX_FILE_SIZES[file_category]
    }

# Add this helper function in main.py
def cleanup_orphaned_media(db: Session):
    """Remove media files that are no longer referenced by any posts"""
    orphaned_media = db.query(models.Media).filter(
        ~models.Media.posts.any()  # Media that has no associated posts
    ).all()
    
    for media in orphaned_media:
        db.delete(media)
    
    db.commit()
    return len(orphaned_media)

# Add this validation function
def validate_media_post_compatibility(media: models.Media, post_feather: str):
    """Ensure media type is compatible with post feather type"""
    if not media or not post_feather:
        return True
        
    media_category = None
    for category, mime_types in ALLOWED_MIME_TYPES.items():
        if media.content_type in mime_types:
            media_category = category
            break
    
    compatibility_map = {
        'photo': 'image',
        'audio': 'audio', 
        'video': 'video'
    }
    
    expected_category = compatibility_map.get(post_feather)
    if expected_category and media_category != expected_category:
        raise HTTPException(
            status_code=400, 
            detail=f"Media type {media_category} is not compatible with post type {post_feather}"
        )

# ===============================================================================
# 3. API ENDPOINTS DEFINED IN MAIN.PY
# ===============================================================================
@app.get("/", tags=["Default"])
def read_root():
    return {"message": "Welcome to the Chyrp Clone API!"}

# --- Authentication Endpoint ---
# In main.py, replace your existing /token endpoint with this

@app.post("/token", tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_email = form_data.username
    user_password = form_data.password

    try:
        response = supabase.auth.sign_in_with_password({
            "email": user_email,
            "password": user_password,
        })
        
        access_token = response.session.access_token
        
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        # Check if it's an authentication error
        error_message = str(e)
        if "Invalid login credentials" in error_message or "invalid" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during login.",
            )

# --- Users Endpoints ---
@app.post("/users/", response_model=schemas.UserModel, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists in your local DB
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    try:
        # Step 1: Create the user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not create user in Supabase: {e}")

    # Step 2: Create the user in your own database
    member_group = db.query(models.Group).filter(models.Group.name == "Member").first()
    if not member_group:
        raise HTTPException(status_code=500, detail="Default 'Member' group not found.")
    
    # Note: We don't store the password hash here anymore because Supabase handles it.
    # You could store the Supabase user ID for future reference.
    # supabase_user_id = auth_response.user.id
    db_user = models.User(
        login=user.login, 
        email=user.email, 
        full_name=user.full_name, 
        group_id=member_group.id
        # You may want to add a column to your User model for the Supabase user ID
        # supabase_id=supabase_user_id 
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=schemas.UserModel, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# --- Groups Endpoints ---
@app.post("/groups/", response_model=schemas.GroupModel, tags=["Groups"])
def create_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["add_group"]))
):
    # Check if group already exists
    existing_group = db.query(models.Group).filter(models.Group.name == group.name).first()
    if existing_group:
        raise HTTPException(status_code=400, detail="Group with this name already exists")
    
    db_group = models.Group(name=group.name, permissions=group.permissions)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.get("/groups/", response_model=List[schemas.GroupModel], tags=["Groups"])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    groups = db.query(models.Group).offset(skip).limit(limit).all()
    return groups

# --- Posts/Pages Endpoints ---
@app.post("/posts/", response_model=schemas.PostModel, tags=["Posts"])
def create_post(
    post: schemas.PostCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["add_post"]))
):
    # Prevent duplicate slug (clean)
    existing = db.query(models.Post).filter(models.Post.clean == post.clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")
    
    # Validate media if provided
    if hasattr(post, 'media_id') and post.media_id:
        media = db.query(models.Media).filter(models.Media.id == post.media_id).first()
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        
        # Security check: ensure user owns the media or has admin permissions
        if media.user_id != current_user.id and "edit_post" not in current_user.group.permissions:
            raise HTTPException(status_code=403, detail="You can only attach media you uploaded")
        
        # Validate media compatibility with post type
        if post.feather:
            validate_media_post_compatibility(media, post.feather)
        
    db_post = models.Post(**post.dict(), user_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.post("/posts/quote", response_model=schemas.PostModel, tags=["Posts"])
async def create_quote_post(
    clean: str = Form(...),
    quote: str = Form(...),
    attribution: str = Form(...),
    status: str = Form("public"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["add_post"]))
):
    # Prevent duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Create quote body with attribution
    quote_body = f'"{quote}"\n\nâ€" {attribution}'

    # Create a post with feather 'quote'
    db_post = models.Post(
        content_type="post",
        feather="quote",
        title=None,  # Quotes typically don't have titles
        body=quote_body,
        clean=clean,
        status=status,
        user_id=current_user.id,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.post("/posts/link", response_model=schemas.PostModel, tags=["Posts"])
async def create_link_post(
    clean: str = Form(...),
    title: str = Form(...),
    url: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form("public"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["add_post"]))
):
    # Prevent duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    # Create link body with description
    link_body = f'**{title}**\n\n[{url}]({url})'
    if description:
        link_body += f'\n\n{description}'

    # Create a post with feather 'link'
    db_post = models.Post(
        content_type="post",
        feather="link",
        title=title,
        body=link_body,
        clean=clean,
        status=status,
        user_id=current_user.id,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.put("/posts/{post_id}/media", response_model=schemas.PostModel, tags=["Posts"])
async def update_post_media(
    post_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    db_post: models.Post = Depends(require_post_permission("edit_post", "edit_own_post")),
    current_user: models.User = Depends(get_current_user)
):
    # Validate file type
    file_info = validate_file_upload(file)
    
    # Read and validate file
    file_content = await file.read()
    if len(file_content) > file_info['max_size']:
        max_mb = file_info['max_size'] // (1024 * 1024)
        raise HTTPException(
            status_code=413, 
            detail=f"{file_info['category'].title()} files must be under {max_mb}MB"
        )
    
    # Create new media record
    db_media = models.Media(
        filename=file.filename,
        original_name=file.filename,
        content_type=file.content_type,
        file_size=len(file_content),
        file_data=file_content,
        user_id=current_user.id
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    
    # Validate media compatibility with post type
    if db_post.feather:
        validate_media_post_compatibility(db_media, db_post.feather)
    
    # Store old media_id for cleanup
    old_media_id = db_post.media_id
    
    # Update post with new media
    db_post.media_id = db_media.id
    db_post.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_post)
    
    # Clean up old media if it exists
    if old_media_id:
        old_media = db.query(models.Media).filter(models.Media.id == old_media_id).first()
        if old_media:
            db.delete(old_media)
            db.commit()
    
    return db_post

@app.delete("/posts/{post_id}/media", response_model=schemas.PostModel, tags=["Posts"])
async def remove_post_media(
    post_id: int,
    db: Session = Depends(get_db),
    db_post: models.Post = Depends(require_post_permission("edit_post", "edit_own_post"))
):
    # Store old media_id for cleanup
    old_media_id = db_post.media_id
    
    # Remove media reference from post
    db_post.media_id = None
    db_post.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_post)
    
    # Clean up the orphaned media
    if old_media_id:
        old_media = db.query(models.Media).filter(models.Media.id == old_media_id).first()
        if old_media:
            db.delete(old_media)
            db.commit()
    
    return db_post

@app.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Media"])
async def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a media file (only if owned by current user or user is admin)"""
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Security check: ensure user owns the media or has admin permissions
    if media.user_id != current_user.id and "delete_post" not in current_user.group.permissions:
        raise HTTPException(status_code=403, detail="You can only delete media you uploaded")
    
    # Check if media is being used by any posts
    posts_using_media = db.query(models.Post).filter(models.Post.media_id == media_id).all()
    if posts_using_media:
        post_titles = [post.title or f"Post #{post.id}" for post in posts_using_media]
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete media: it's being used by posts: {', '.join(post_titles)}"
        )
    
    db.delete(media)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Optional: Add an admin endpoint to trigger cleanup
@app.delete("/admin/cleanup-media", dependencies=[Depends(require_permission(["delete_user"]))])
def cleanup_orphaned_media_endpoint(db: Session = Depends(get_db)):
    """Admin endpoint to clean up orphaned media files"""
    count = cleanup_orphaned_media(db)
    return {"message": f"Cleaned up {count} orphaned media files"}
    db.refresh(db_post)
    return db_post

@app.get("/posts/", response_model=List[schemas.PostModel], tags=["Posts"])
def read_posts(content_type: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # FIX: Add .options(joinedload(models.Post.media)) to the query
    query = db.query(models.Post).options(joinedload(models.Post.media))
    
    if content_type:
        query = query.filter(models.Post.content_type == content_type)
        
    posts = query.order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

@app.get("/posts/{post_id}", response_model=schemas.PostModel, tags=["Posts"])
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@app.put("/posts/{post_id}", response_model=schemas.PostModel, tags=["Posts"])
def update_post(
    post_id: int,
    post_update: schemas.PostUpdate, 
    db: Session = Depends(get_db),
    db_post: models.Post = Depends(require_post_permission("edit_post", "edit_own_post")),
    current_user: models.User = Depends(get_current_user)
):
    # --- START: NEW LOGIC - Prevent editing posts with media ---
    # Check if the post being updated has media attached.
    if db_post.media_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Posts with media cannot be edited. You can only delete them."
        )
    # --- END: NEW LOGIC ---
    
    # Handle media_id validation if it's being updated
    if post_update.media_id is not None:
        if post_update.media_id != 0:  # 0 or None could mean "remove media"
            media = db.query(models.Media).filter(models.Media.id == post_update.media_id).first()
            if not media:
                raise HTTPException(status_code=404, detail="Media not found")
            
            # Security check: ensure user owns the media or has admin permissions
            if media.user_id != current_user.id and "edit_post" not in current_user.group.permissions:
                raise HTTPException(status_code=403, detail="You can only attach media you uploaded")
            
            # Validate media compatibility with post type
            if post_update.feather:
                validate_media_post_compatibility(media, post_update.feather)
            elif db_post.feather:
                validate_media_post_compatibility(media, db_post.feather)

    # Update the post with new values
    for key, value in post_update.dict(exclude_unset=True).items():
        if key == "media_id" and value == 0:
            # Handle explicit media removal (if you want to support media_id: 0 as "remove media")
            setattr(db_post, key, None)
        else:
            setattr(db_post, key, value)
    
    db_post.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_post)
    return db_post

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Posts"])
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    db_post: models.Post = Depends(require_post_permission("delete_post", "delete_own_post"))
):
    # The dependency already verified permissions and fetched the post.
    # Store media_id for cleanup
    media_id = db_post.media_id
    
    # Delete the post
    db.delete(db_post)
    db.commit()
    
    # Clean up associated media if it exists
    if media_id:
        media = db.query(models.Media).filter(models.Media.id == media_id).first()
        if media:
            db.delete(media)
            db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ===============================================================================
# 4. UPLOAD ENDPOINTS
# ===============================================================================

@app.post("/upload", tags=["Uploads"])
async def upload_file(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user)
):
    # Validate file type
    validate_file_upload(file)
    
    # Ensure uploads directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique filename preserving extension
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/uploads/{unique_name}"
    return {"url": file_url, "filename": file.filename}

@app.post("/upload-to-db", response_model=MediaModel, tags=["Uploads"])
async def upload_file_to_database(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Validate file type
    file_info = validate_file_upload(file)
    
    # Read file content
    file_content = await file.read()
    
    # Validate file size
    if len(file_content) > file_info['max_size']:
        max_mb = file_info['max_size'] // (1024 * 1024)
        raise HTTPException(
            status_code=413, 
            detail=f"{file_info['category'].title()} files must be under {max_mb}MB"
        )
    
    # Create media record
    db_media = models.Media(
        filename=file.filename,
        original_name=file.filename,
        content_type=file.content_type,
        file_size=len(file_content),
        file_data=file_content,
        user_id=current_user.id
    )
    
    db.add(db_media)
    db.commit()
    db.refresh(db_media)
    
    return db_media

@app.get("/media/{media_id}", tags=["Media"])
async def get_media_file(media_id: int, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Determine if it's streamable content
    streamable_types = [
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg',
        'video/mp4', 'video/webm'
    ]
    
    headers = {
        "Content-Disposition": f"inline; filename={media.filename}",
        "Content-Length": str(media.file_size),
    }
    
    # Add streaming headers for audio/video
    if media.content_type in streamable_types:
        headers.update({
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        })
    
    return Response(
        content=media.file_data,
        media_type=media.content_type,
        headers=headers
    )

@app.get("/media/{media_id}/info", response_model=MediaModel, tags=["Media"])
async def get_media_info(media_id: int, db: Session = Depends(get_db)):
    media = db.query(models.Media).filter(models.Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    return media

@app.get("/media/", response_model=List[MediaModel], tags=["Media"])
async def get_user_media(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get all media files uploaded by the current user"""
    media_files = db.query(models.Media).filter(
        models.Media.user_id == current_user.id
    ).order_by(models.Media.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return media_files

# --- Media Post Endpoints ---

@app.post("/posts/photo-db", response_model=schemas.PostModel, tags=["Posts"])
async def create_photo_post_with_db_storage(
    clean: str = Form(...),
    title: Optional[str] = Form(None),
    status: str = Form("public"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
        token: str = Depends(oauth2_scheme) ,
    _: None = Depends(require_permission(["add_post"]))
):
    # Validate image type
    file_info = validate_file_upload(file, expected_type="image")
    
    # Check for duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Upload to Supabase Storage
    file_content = await file.read()
    if len(file_content) > file_info['max_size']:
        raise HTTPException(status_code=413, detail="Image file too large")

    # Reset file pointer before passing to helper
    await file.seek(0) 

    # Upload to Supabase using the helper function
    public_url = await upload_file_to_supabase(file, "media_uploads", token)

    # Save the URL to your database
    db_media = models.Media(
        filename=file.filename,
        original_name=file.filename,
        content_type=file.content_type,
        file_size=len(file_content),
        file_url=public_url,  # Store the URL, not the data
        user_id=current_user.id
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)

    # Create post with media reference
    db_post = models.Post(
        content_type="post",
        feather="photo",
        title=title,
        body=f"Image: {file.filename}",
        clean=clean,
        status=status,
        media_id=db_media.id,
        user_id=current_user.id,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

@app.post("/posts/audio", response_model=schemas.PostModel, tags=["Posts"])
async def create_audio_post(
    clean: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form("public"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["add_post"]))
):
    # Validate audio file
    file_info = validate_file_upload(file, expected_type="audio")
    
    # Check for duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Read and store file in database
    file_content = await file.read()
    
    if len(file_content) > file_info['max_size']:
        raise HTTPException(status_code=413, detail="Audio file too large")
    
    db_media = models.Media(
        filename=file.filename,
        original_name=file.filename,
        content_type=file.content_type,
        file_size=len(file_content),
        file_data=file_content,
        user_id=current_user.id
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)

    # Create audio post body
    audio_body = f"**{title}**"
    if description:
        audio_body += f"\n\n{description}"

    # Create post with media reference
    db_post = models.Post(
        content_type="post",
        feather="audio",
        title=title,
        body=audio_body,
        clean=clean,
        status=status,
        media_id=db_media.id,
        user_id=current_user.id,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

@app.post("/posts/video", response_model=schemas.PostModel, tags=["Posts"])
async def create_video_post(
    clean: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form("public"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["add_post"]))
):
    # Validate video file
    file_info = validate_file_upload(file, expected_type="video")
    
    # Check for duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Read and store file in database
    file_content = await file.read()
    
    if len(file_content) > file_info['max_size']:
        raise HTTPException(status_code=413, detail="Video file too large")
    
    db_media = models.Media(
        filename=file.filename,
        original_name=file.filename,
        content_type=file.content_type,
        file_size=len(file_content),
        file_data=file_content,
        user_id=current_user.id
    )
    db.add(db_media)
    db.commit()
    db.refresh(db_media)

    # Create video post body
    video_body = f"**{title}**"
    if description:
        video_body += f"\n\n{description}"

    # Create post with media reference
    db_post = models.Post(
        content_type="post",
        feather="video",
        title=title,
        body=video_body,
        clean=clean,
        status=status,
        media_id=db_media.id,
        user_id=current_user.id,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

# --- Legacy Filesystem Endpoints (kept for backwards compatibility) ---

@app.post("/posts/photo", response_model=schemas.PostModel, tags=["Posts"])
async def create_photo_post(
    clean: str = Form(...),
    title: Optional[str] = Form(None),
    status: str = Form("public"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(require_permission(["add_post"]))
):
    # Validate image type
    validate_file_upload(file, expected_type="image")
    
    # Prevent duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Save file to filesystem
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/uploads/{unique_name}"

    # Create a post whose body is the image URL and feather is 'photo'
    db_post = models.Post(
        content_type="post",
        feather="photo",
        title=title,
        body=file_url,
        clean=clean,
        status=status,
        user_id=current_user.id,
    )
    db.add(db_post)
    db