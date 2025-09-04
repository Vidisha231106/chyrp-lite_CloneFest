# main.py

import datetime
from typing import List, Optional

from dotenv import load_dotenv
from supabase import create_client, Client

# Add upload-related imports
from fastapi import UploadFile, File, Form
import os
from uuid import uuid4

import google.generativeai as genai

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# --- Import from our custom files ---
import models
import schemas
from database import engine, SessionLocal
from dependencies import (
    get_db, 
    get_current_user, 
    create_access_token, 
    get_password_hash, 
    verify_password,
    require_permission,      # <-- ADD THIS IMPORT
    require_post_permission  # <-- EXISTING IMPORT
)
from routers import interactions

# ===============================================================================
# 1. FASTAPI APP INITIALIZATION & MIDDLEWARE
# ===============================================================================
app = FastAPI(
    title="Chyrp Clone API",
    description="API for the modern Chyrp blogging engine.",
    version="1.0.0",
)

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- NEW: Configure Google AI ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise Exception("Google API Key not found in .env file")
genai.configure(api_key=GOOGLE_API_KEY)
generation_config = genai.GenerationConfig(temperature=0.7)
ai_model = genai.GenerativeModel('gemini-1.5-flash-latest', generation_config=generation_config)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not found in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "media_uploads"  # The name of the bucket you created in Supabase


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
            admin_permissions = ["edit_post", "delete_post", "add_user", "edit_user", "delete_user", "add_group", "edit_group", "delete_group", "like_post", "add_post", "edit_own_post", "delete_own_post"]  # Added missing permissions for admin
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

# ===============================================================================
# 3. API ENDPOINTS DEFINED IN MAIN.PY
# ===============================================================================
@app.get("/", tags=["Default"])
def read_root():
    return {"message": "Welcome to the Chyrp Clone API!"}

# --- NEW: AI Enhancement Endpoint ---
@app.post("/ai/enhance", response_model=schemas.AIEnhanceResponse, tags=["AI"])
async def enhance_text_with_ai(
    request: schemas.AIEnhanceRequest,
    current_user: models.User = Depends(get_current_user)
):
    """
    Enhances a given text using the Gemini Pro AI model.
    """
    try:
        # Construct the full prompt for the AI
        full_prompt = f"{request.prompt}\n\n---\n\n{request.text}"
        
        # Generate content using the AI model
        response = ai_model.generate_content(full_prompt)
        
        # Check if the response contains text
        if not response.parts:
            raise HTTPException(status_code=500, detail="AI failed to generate a response.")
            
        enhanced_text = response.text
        
        return schemas.AIEnhanceResponse(enhanced_text=enhanced_text)

    except Exception as e:
        # Log the error for debugging
        print(f"AI generation failed: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while communicating with the AI service.")

# --- Authentication Endpoint ---
@app.post("/token", tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.login == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.login})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Users Endpoints ---
@app.post("/users/", response_model=schemas.UserModel, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    member_group = db.query(models.Group).filter(models.Group.name == "Member").first()
    if not member_group:
        raise HTTPException(status_code=500, detail="Default 'Member' group not found.")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(login=user.login, email=user.email, full_name=user.full_name, hashed_password=hashed_password, group_id=member_group.id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=schemas.UserModel, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# --- Groups Endpoints ---
@app.post("/groups/", response_model=schemas.GroupModel, tags=["Groups"])
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
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
    _: None = Depends(require_permission(["add_post"]))  # <-- ADD THIS PERMISSION CHECK
):
    # Prevent duplicate slug (clean)
    existing = db.query(models.Post).filter(models.Post.clean == post.clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")
        
    db_post = models.Post(**post.dict(), user_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/posts/", response_model=List[schemas.PostModel], tags=["Posts"])
def read_posts(content_type: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Post)
    if content_type:
        query = query.filter(models.Post.content_type == content_type)
    posts = query.offset(skip).limit(limit).all()
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
    db_post: models.Post = Depends(require_post_permission("edit_post", "edit_own_post"))
):
    # The dependency already verified permissions and fetched the post.
    # We can now safely update it.
    for key, value in post_update.dict(exclude_unset=True).items():
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
    # We can now safely delete it.
    db.delete(db_post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ===============================================================================
# 4. UPLOAD ENDPOINTS
# ===============================================================================

@app.post("/upload", tags=["Uploads"])
async def upload_file(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user)):
    # --- MODIFIED: Replaced local file saving with Supabase upload ---
    
    # Generate unique filename preserving extension
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    
    try:
        # Read file content into memory
        contents = await file.read()

        # Upload to Supabase Storage
        supabase.storage.from_(BUCKET_NAME).upload(
            path=unique_name, 
            file=contents,
            file_options={"content-type": file.content_type}
        )

        # Get the public URL
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    
    finally:
        await file.close()

    return {"url": file_url, "filename": file.filename}


@app.post("/posts/photo", response_model=schemas.PostModel, tags=["Posts"])
async def create_photo_post(
    clean: str = Form(...),
    title: Optional[str] = Form(None),
    status: str = Form("public"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Prevent duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # --- MODIFIED: Replaced local file saving with Supabase upload ---
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"

    try:
        contents = await file.read()
        supabase.storage.from_(BUCKET_NAME).upload(
            path=unique_name,
            file=contents,
            file_options={"content-type": file.content_type}
        )
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    
    finally:
        await file.close()

    # Create a post whose body is the image URL from Supabase
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
):
    # Prevent duplicate slug
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Create quote body with attribution
    quote_body = f'"{quote}"\n\n— {attribution}'

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