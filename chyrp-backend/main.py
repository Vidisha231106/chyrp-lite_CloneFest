# main.py

import datetime
from typing import List, Optional
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from sqlalchemy import or_, and_
from utils import generate_excerpt, create_slug
from models import Group, User, Category, Post, Tag
# Add upload-related imports
from fastapi import UploadFile, File, Form
import os
from uuid import uuid4

import google.generativeai as genai  # Temporarily commented out for testing

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
    get_optional_current_user,
    require_post_permission  # <-- EXISTING IMPORT
)
from routers import interactions, comments, tags, categories, views, maptcha, highlighter, lightbox, cascade, embed, mentionable, mathjax, search
from cache import setup_cache, cache_for_5_minutes, cache_for_1_hour
from utils import generate_excerpt

# ===============================================================================
# 1. FASTAPI APP INITIALIZATION & MIDDLEWARE
# ===============================================================================
app = FastAPI(
    title="Chyrp Clone API",
    description="API for the modern Chyrp blogging engine.",
    version="1.0.0",
)

load_dotenv()
# Supabase configuration for both database and storage
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://localhost:5173")

# --- NEW: Configure Google AI ---
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     raise Exception("Google API Key not found in .env file")
# genai.configure(api_key=GOOGLE_API_KEY)
# generation_config = genai.GenerationConfig(temperature=0.7)
# ai_model = genai.GenerativeModel('gemini-1.5-flash-latest', generation_config=generation_config)


if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials not found in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET_NAME = "media_uploads"  # The name of the bucket you created in Supabase


# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
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
app.include_router(comments.router)
app.include_router(tags.router)
app.include_router(categories.router)
app.include_router(views.router)
app.include_router(maptcha.router)
app.include_router(highlighter.router)
app.include_router(lightbox.router)
app.include_router(cascade.router)
app.include_router(embed.router)
app.include_router(mentionable.router)
app.include_router(mathjax.router)
app.include_router(search.router)

# --- Create Database Tables on Startup ---
models.Base.metadata.create_all(bind=engine)

# --- Setup Cache ---
setup_cache()

# ===============================================================================
# 2. STARTUP EVENT (DATABASE SEEDING)
# ===============================================================================
@app.on_event("startup")
def create_initial_data():
    db = SessionLocal()
    try:
        print("🚀 Checking and seeding initial database data...")

        # --- Define required permissions ---
        admin_permissions_set = {
            "edit_post", "delete_post", "add_user", "edit_user", "delete_user",
            "add_group", "edit_group", "delete_group", "like_post", "add_post",
            "edit_own_post", "delete_own_post"
        }
        member_permissions_set = {
            "add_post", "edit_own_post", "delete_own_post", "like_post"
        }

        # --- Check and Create/Update Admin Group ---
        admin_group = db.query(models.Group).filter(models.Group.name == "Admin").first()
        if not admin_group:
            print("Creating 'Admin' group...")
            admin_group = models.Group(name="Admin", permissions=list(admin_permissions_set))
            db.add(admin_group)
        else:
            # If group exists, ensure all permissions are present
            current_permissions = set(admin_group.permissions)
            if not admin_permissions_set.issubset(current_permissions):
                print("Updating 'Admin' group with missing permissions...")
                missing = admin_permissions_set - current_permissions
                admin_group.permissions.extend(list(missing))

        # --- Check and Create/Update Member Group ---
        member_group = db.query(models.Group).filter(models.Group.name == "Member").first()
        if not member_group:
            print("Creating 'Member' group...")
            member_group = models.Group(name="Member", permissions=list(member_permissions_set))
            db.add(member_group)
        else:
            # If group exists, ensure all permissions are present
            current_permissions = set(member_group.permissions)
            if not member_permissions_set.issubset(current_permissions):
                print("Updating 'Member' group with missing permissions...")
                missing = member_permissions_set - current_permissions
                member_group.permissions.extend(list(missing))
        
        db.commit()
        db.refresh(admin_group)
        db.refresh(member_group)
        
        # --- Check and Create Admin User ---
        if not db.query(models.User).filter(models.User.login == "admin").first():
            print("Creating default 'admin' user...")
            hashed_password = get_password_hash("admin")
            admin_user = models.User(
                login="admin",
                email="admin@example.com",
                full_name="Administrator",
                hashed_password=hashed_password,
                group_id=admin_group.id
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            # Create Static Pages only when admin is first created
            if not db.query(models.Post).filter(models.Post.clean == "about-us").first():
                about_page = models.Post(content_type="page", title="About Us", body="## Welcome!\n\nThis is the default 'About Us' page.", clean="about-us", status="public", user_id=admin_user.id)
                db.add(about_page)
            if not db.query(models.Post).filter(models.Post.clean == "contact").first():
                contact_page = models.Post(content_type="page", title="Contact", body="This is the default 'Contact' page.", clean="contact", status="public", user_id=admin_user.id)
                db.add(contact_page)
            db.commit()
        
        print("✅ Initial data check completed successfully.")
    
        print("Seeding categories...")
        
        REQUIRED_CATEGORIES = [
            "Education", "Tech", "Fashion", "Food", "Travel", 
            "News", "Experiences", "Opinions", "Misc"
        ]

        for cat_name in REQUIRED_CATEGORIES:
            # Check if the category already exists
            exists = db.query(Category).filter(Category.name == cat_name).first()
            if not exists:
                # If it doesn't exist, create it
                new_cat = Category(
                    name=cat_name,
                    slug=create_slug(cat_name) # create_slug utility generates the URL part
                )
                db.add(new_cat)
                print(f"Created category: {cat_name}")
        
        db.commit()
    
    except Exception as e:
        print(f"❌ An error occurred during initial data seeding: {e}")
        db.rollback() # Rollback changes on error
    finally:
        db.close()

# ===============================================================================
# 3. API ENDPOINTS DEFINED IN MAIN.PY
# ===============================================================================
@app.get("/", tags=["Default"])
def read_root():
    return {"message": "Welcome to the Chyrp Clone API!"}

# --- NEW: AI Enhancement Endpoint ---
# @app.post("/ai/enhance", response_model=schemas.AIEnhanceResponse, tags=["AI"])
# async def enhance_text_with_ai(
#     request: schemas.AIEnhanceRequest,
#     current_user: models.User = Depends(get_current_user)
# ):
#     """
#     Enhances a given text using the Gemini Pro AI model.
#     """
#     try:
#         # Construct the full prompt for the AI
#         full_prompt = f"{request.prompt}\n\n---\n\n{request.text}"
#         
#         # Generate content using the AI model
#         response = ai_model.generate_content(full_prompt)
#         
#         # Check if the response contains text
#         if not response.parts:
#             raise HTTPException(status_code=500, detail="AI failed to generate a response.")
#             
#         enhanced_text = response.text
#         
#         return schemas.AIEnhanceResponse(enhanced_text=enhanced_text)
# 
#     except Exception as e:
#         # Log the error for debugging
#         print(f"AI generation failed: {e}")
#         raise HTTPException(status_code=500, detail="An error occurred while communicating with the AI service.")

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
    # Add is_active=True to the user creation
    db_user = models.User(
        login=user.login, 
        email=user.email, 
        full_name=user.full_name, 
        hashed_password=hashed_password, 
        group_id=member_group.id,
        is_active=True  # <-- ADD THIS LINE
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=schemas.UserModel, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Test endpoint to check authentication
@app.get("/test-auth", tags=["Test"])
async def test_auth(current_user: Optional[models.User] = Depends(get_optional_current_user)):
    if current_user:
        return {"message": f"Hello {current_user.login}!", "authenticated": True}
    else:
        return {"message": "Not authenticated", "authenticated": False}

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

# main.py

@app.post("/posts/", response_model=schemas.PostModel, tags=["Posts"])
def create_post(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Prevent duplicate slug (clean)
    existing = db.query(models.Post).filter(models.Post.clean == post.clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")
    
    post_data = post.dict()
    
    # --- Handle Tags (find or create) ---
    tag_names = post_data.pop('tags', [])
    final_tags = []
    if tag_names:
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            db_tag = db.query(models.Tag).filter(models.Tag.name.ilike(name)).first()
            if not db_tag:
                db_tag = models.Tag(name=name, slug=create_slug(name))
                db.add(db_tag)
                # Commit here to get an ID for the new tag if needed by other logic
                db.commit()
                db.refresh(db_tag)
            final_tags.append(db_tag)

    # --- Handle Categories (fetch by ID) ---
    category_ids = post_data.pop('category_ids', [])
    final_categories = []
    if category_ids:
        final_categories = db.query(models.Category).filter(models.Category.id.in_(category_ids)).all()

    # Auto-generate excerpt if not provided
    if not post_data.get('excerpt') and post_data.get('body'):
        post_data['excerpt'] = generate_excerpt(post_data['body'])

    # Create the Post instance
    db_post = models.Post(**post_data, user_id=current_user.id)
    
    # Associate the tags and categories
    db_post.tags = final_tags
    db_post.categories = final_categories
    
    # Add, commit, and refresh the final post object
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

# --- MODIFIED: Update the read_posts endpoint ---
@app.get("/posts/", response_model=List[schemas.PostModel], tags=["Posts"])
#@cache_for_5_minutes()
def read_posts(
    content_type: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_current_user) # <-- USE NEW DEPENDENCY
):
    query = db.query(models.Post)

    if current_user:
        # If user is logged in, show them all public posts OR their own drafts
        query = query.filter(
            or_(
                models.Post.status == 'public',
                and_(
                    models.Post.user_id == current_user.id,
                    models.Post.status == 'draft'
                )
            )
        )
    else:
        # If user is not logged in, only show public posts
        query = query.filter(models.Post.status == 'public')

    if content_type:
        query = query.filter(models.Post.content_type == content_type)
    
    # Order by creation date, newest first, before applying pagination
    posts = query.order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

@app.get("/posts/{post_id}", response_model=schemas.PostModel, tags=["Posts"])
@cache_for_5_minutes()
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
    tags: str = Form('[]'),
    category_ids: str = Form('[]'),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Upload file to Supabase (your existing logic is correct)
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    try:
        contents = await file.read()
        supabase.storage.from_(BUCKET_NAME).upload(path=unique_name, file=contents, file_options={"content-type": file.content_type})
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    finally:
        await file.close()

    db_post = models.Post(
        feather="photo", title=title, body=file_url, clean=clean,
        status=status, user_id=current_user.id
    )
    db.add(db_post)

    # --- ADD THIS LOGIC TO ATTACH TAGS AND CATEGORIES ---
    tag_names = json.loads(tags)
    final_tags = []
    if tag_names:
        for name in tag_names:
            db_tag = db.query(models.Tag).filter(models.Tag.name.ilike(name.strip())).first()
            if not db_tag:
                db_tag = models.Tag(name=name.strip(), slug=create_slug(name.strip()))
                db.add(db_tag)
            final_tags.append(db_tag)
    db_post.tags = final_tags

    category_ids_list = json.loads(category_ids)
    if category_ids_list:
        db_post.categories = db.query(models.Category).filter(models.Category.id.in_(category_ids_list)).all()
    # --- END OF NEW LOGIC ---

    db.commit()
    db.refresh(db_post)
    return db_post

@app.post("/posts/quote", response_model=schemas.PostModel, tags=["Posts"])
async def create_quote_post(
    clean: str = Form(...),
    quote: str = Form(...),
    attribution: str = Form(...),
    status: str = Form("public"),
    tags: str = Form('[]'),
    category_ids: str = Form('[]'),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    quote_body = f'"{quote}"\n\n— {attribution}'
    db_post = models.Post(
        feather="quote", body=quote_body, clean=clean,
        status=status, user_id=current_user.id
    )
    db.add(db_post)
    
    # --- ADD THIS LOGIC TO ATTACH TAGS AND CATEGORIES ---
    tag_names = json.loads(tags)
    final_tags = []
    if tag_names:
        for name in tag_names:
            db_tag = db.query(models.Tag).filter(models.Tag.name.ilike(name.strip())).first()
            if not db_tag:
                db_tag = models.Tag(name=name.strip(), slug=create_slug(name.strip()))
                db.add(db_tag)
            final_tags.append(db_tag)
    db_post.tags = final_tags

    category_ids_list = json.loads(category_ids)
    if category_ids_list:
        db_post.categories = db.query(models.Category).filter(models.Category.id.in_(category_ids_list)).all()
    # --- END OF NEW LOGIC ---

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
    tags: str = Form('[]'),
    category_ids: str = Form('[]'),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    link_body = url
    if description:
        link_body += f'\n\n{description}'
        
    db_post = models.Post(
        feather="link", title=title, body=link_body, clean=clean,
        status=status, user_id=current_user.id
    )
    db.add(db_post)
    
    # --- ADD THIS LOGIC TO ATTACH TAGS AND CATEGORIES ---
    tag_names = json.loads(tags)
    final_tags = []
    if tag_names:
        for name in tag_names:
            db_tag = db.query(models.Tag).filter(models.Tag.name.ilike(name.strip())).first()
            if not db_tag:
                db_tag = models.Tag(name=name.strip(), slug=create_slug(name.strip()))
                db.add(db_tag)
            final_tags.append(db_tag)
    db_post.tags = final_tags

    category_ids_list = json.loads(category_ids)
    if category_ids_list:
        db_post.categories = db.query(models.Category).filter(models.Category.id.in_(category_ids_list)).all()
    # --- END OF NEW LOGIC ---
    
    db.commit()
    db.refresh(db_post)
    return db_post


@app.post("/posts/video", response_model=schemas.PostModel, tags=["Posts"])
async def create_video_post(
    clean: str = Form(...),
    title: Optional[str] = Form(None),
    status: str = Form("public"),
    tags: str = Form('[]'),
    category_ids: str = Form('[]'),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Upload logic remains the same...
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    try:
        contents = await file.read()
        supabase.storage.from_(BUCKET_NAME).upload(path=unique_name, file=contents, file_options={"content-type": file.content_type})
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    finally:
        await file.close()

    db_post = models.Post(
        feather="video", title=title, body=file_url, clean=clean,
        status=status, user_id=current_user.id
    )
    db.add(db_post)

    # --- ADD THIS LOGIC TO ATTACH TAGS AND CATEGORIES ---
    tag_names = json.loads(tags)
    final_tags = []
    if tag_names:
        for name in tag_names:
            db_tag = db.query(models.Tag).filter(models.Tag.name.ilike(name.strip())).first()
            if not db_tag:
                db_tag = models.Tag(name=name.strip(), slug=create_slug(name.strip()))
                db.add(db_tag)
            final_tags.append(db_tag)
    db_post.tags = final_tags

    category_ids_list = json.loads(category_ids)
    if category_ids_list:
        db_post.categories = db.query(models.Category).filter(models.Category.id.in_(category_ids_list)).all()
    # --- END OF NEW LOGIC ---
    
    db.commit()
    db.refresh(db_post)
    return db_post


@app.post("/posts/audio", response_model=schemas.PostModel, tags=["Posts"])
async def create_audio_post(
    clean: str = Form(...),
    title: Optional[str] = Form(None),
    status: str = Form("public"),
    tags: str = Form('[]'),
    category_ids: str = Form('[]'),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Post).filter(models.Post.clean == clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="A post with this slug already exists.")

    # Upload logic remains the same...
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid4().hex}{ext}"
    try:
        contents = await file.read()
        supabase.storage.from_(BUCKET_NAME).upload(path=unique_name, file=contents, file_options={"content-type": file.content_type})
        file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    finally:
        await file.close()

    db_post = models.Post(
        feather="audio", title=title, body=file_url, clean=clean,
        status=status, user_id=current_user.id
    )
    db.add(db_post)
    
    # --- ADD THIS LOGIC TO ATTACH TAGS AND CATEGORIES ---
    tag_names = json.loads(tags)
    final_tags = []
    if tag_names:
        for name in tag_names:
            db_tag = db.query(models.Tag).filter(models.Tag.name.ilike(name.strip())).first()
            if not db_tag:
                db_tag = models.Tag(name=name.strip(), slug=create_slug(name.strip()))
                db.add(db_tag)
            final_tags.append(db_tag)
    db_post.tags = final_tags

    category_ids_list = json.loads(category_ids)
    if category_ids_list:
        db_post.categories = db.query(models.Category).filter(models.Category.id.in_(category_ids_list)).all()
    # --- END OF NEW LOGIC ---
    
    db.commit()
    db.refresh(db_post)
    return db_post

@app.post("/uploads/multi", tags=["Uploads"])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: models.User = Depends(get_current_user)
):
    """Upload multiple files to Supabase Storage and return their public URLs."""
    urls = []
    for file in files:
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
            urls.append({"url": file_url, "filename": file.filename})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading {file.filename}: {str(e)}")
        finally:
            await file.close()
    return {"files": urls}

@app.get("/sitemap.xml", tags=["SEO"]) 
def sitemap(db: Session = Depends(get_db)):
    """Generate a simple sitemap for public posts and pages."""
    posts = db.query(models.Post).filter(models.Post.status == 'public').order_by(models.Post.updated_at.desc()).all()

    url_items = []
    generated_at = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    for post in posts:
        # Prefer clean slug if available; fall back to id route
        path = f"/post/{post.id}"
        if post.clean:
            # Example frontend route assumption: /p/{clean}
            path = f"/p/{post.clean}"
        url_items.append(f"""
  <url>
    <loc>{SITE_BASE_URL}{path}</loc>
    <lastmod>{post.updated_at.strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{'1.0' if post.pinned else '0.5'}</priority>
  </url>""")

    xml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\"> 
  <url>
    <loc>{SITE_BASE_URL}</loc>
    <lastmod>{generated_at}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>{''.join(url_items)}
</urlset>"""

    return Response(content=xml.strip(), media_type="application/xml")

@app.get("/posts/by-category/{category_id}", response_model=List[schemas.PostModel], tags=["Posts"])
def get_posts_by_category_id(
    category_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get posts filtered by category ID."""
    posts = db.query(models.Post).join(models.Post.categories).filter(
        models.Category.id == category_id,
        models.Post.status == 'public'
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

@app.get("/posts/by-tag/{tag_id}", response_model=List[schemas.PostModel], tags=["Posts"])
def get_posts_by_tag_id(
    tag_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get posts filtered by tag ID."""
    posts = db.query(models.Post).join(models.Post.tags).filter(
        models.Tag.id == tag_id,
        models.Post.status == 'public'
    ).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts