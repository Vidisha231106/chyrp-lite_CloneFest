# API_DOCUMENTATION.md

# Chyrp Lite Clone - Complete Backend API Documentation

## Overview
This document provides comprehensive documentation for all backend features implemented in the Chyrp Lite Clone project.

## Core Features ✅ COMPLETED

### 1. **Read More Module**
- **Purpose**: Auto-generate excerpts from post content for better readability
- **Endpoints**: 
  - Auto-generated excerpts in post creation/update
- **Features**:
  - Automatic excerpt generation from post body
  - Markdown formatting removal
  - Configurable excerpt length (default: 200 characters)
  - Smart word boundary truncation

### 2. **MAPTCHA Spam Prevention**
- **Purpose**: Math-based CAPTCHA system for comment spam prevention
- **Endpoints**:
  - `POST /maptcha/generate` - Generate new challenge
  - `POST /maptcha/verify` - Verify answer
  - `POST /posts/{post_id}/comments/with-maptcha` - Create comment with verification
- **Features**:
  - Simple arithmetic questions (addition, subtraction, multiplication)
  - Hash-based answer verification
  - Comment creation with CAPTCHA validation

### 3. **Highlighter (Syntax Highlighting)**
- **Purpose**: Syntax highlighting for code blocks in posts
- **Endpoints**:
  - `POST /highlighter/analyze` - Analyze post for code blocks
  - `POST /highlighter/highlight` - Highlight code snippet
  - `GET /highlighter/languages` - Get supported languages
- **Features**:
  - Support for 20+ programming languages
  - Automatic language detection
  - Basic syntax highlighting patterns
  - Code block extraction from markdown

### 4. **Lightbox Module**
- **Purpose**: Image gallery functionality with protection
- **Endpoints**:
  - `GET /lightbox/post/{post_id}/images` - Get post images
  - `GET /lightbox/user/{user_id}/gallery` - Get user gallery
  - `GET /lightbox/recent` - Get recent images
  - `POST /lightbox/protect` - Protect image
  - `GET /lightbox/search` - Search images
- **Features**:
  - Image extraction from markdown and HTML
  - User-specific galleries
  - Image protection system
  - Search functionality

### 5. **Cascade (Infinite Scrolling)**
- **Purpose**: Cursor-based pagination for infinite scrolling
- **Endpoints**:
  - `GET /cascade/posts` - Get posts with cursor pagination
  - `GET /cascade/tags/{tag_id}/posts` - Get posts by tag
  - `GET /cascade/categories/{category_id}/posts` - Get posts by category
  - `GET /cascade/user/{user_id}/posts` - Get user posts
- **Features**:
  - Cursor-based pagination
  - Multiple sorting options
  - Tag and category filtering
  - Performance optimized

### 6. **Easy Embed Module**
- **Purpose**: Embed external content (YouTube, Twitter, etc.)
- **Endpoints**:
  - `POST /embed/process` - Process content for embeds
  - `GET /embed/post/{post_id}/processed` - Get post with embeds
  - `POST /embed/validate` - Validate embed URL
  - `GET /embed/platforms` - Get supported platforms
  - `POST /embed/preview` - Preview embed
- **Features**:
  - Support for YouTube, Twitter, Instagram, Vimeo, CodePen
  - Automatic URL detection and conversion
  - Safe iframe rendering
  - Preview functionality

### 7. **Mentionable (Webmentions)**
- **Purpose**: Webmention system for blog interactions
- **Endpoints**:
  - `POST /webmention/receive` - Receive webmention
  - `POST /webmention/send` - Send webmention
  - `POST /webmention/discover` - Discover endpoint
  - `GET /webmention/endpoint` - Get endpoint info
  - `POST /webmention/process-post` - Process post for webmentions
- **Features**:
  - Webmention protocol support
  - Automatic endpoint discovery
  - Link extraction and processing
  - Pingback support

### 8. **MathJax Integration**
- **Purpose**: Mathematical notation rendering
- **Endpoints**:
  - `POST /mathjax/process` - Process content for math
  - `GET /mathjax/post/{post_id}/processed` - Get post with math
  - `POST /mathjax/validate` - Validate math expression
  - `GET /mathjax/config` - Get MathJax config
  - `POST /mathjax/preview` - Preview math expression
- **Features**:
  - LaTeX math support
  - Inline and display math
  - Expression validation
  - MathJax configuration

## Previously Implemented Features ✅ COMPLETED

### **Comments System**
- Complete commenting system with nested comments
- Comment moderation and approval
- User permissions for comment management

### **Tags System**
- Tag creation, management, and association
- Popular tags by post count
- Tag search functionality

### **Categories System**
- Hierarchical category structure
- Category tree organization
- Popular categories by post count

### **Post Views System**
- View count tracking
- Detailed analytics (daily, weekly, monthly)
- Popular posts by view count

### **Video and Audio Content Types**
- Video file uploads to Supabase Storage
- Audio file uploads to Supabase Storage
- Content type management

### **Multi-file Uploader**
- Multiple file uploads to Supabase Storage
- File management and organization

### **Rights and Attribution**
- Copyright and attribution fields
- License information
- Rights management

### **Sitemap Generation**
- XML sitemap for SEO
- Public post inclusion
- Search engine optimization

### **Caching System**
- Redis-based caching
- Configurable cache durations
- Performance optimization

## Database Schema Updates

### **Post Model**
- Added `excerpt` field for Read More functionality
- Enhanced with all new feature support

### **New Models**
- `Comment` - Comment system
- `Tag` - Tag management
- `Category` - Category management
- `PostView` - View tracking

## API Endpoints Summary

### **Core Posts**
- `GET /posts/` - List posts with filtering
- `POST /posts/` - Create post
- `GET /posts/{post_id}` - Get single post
- `PUT /posts/{post_id}` - Update post
- `DELETE /posts/{post_id}` - Delete post
- `POST /posts/video` - Create video post
- `POST /posts/audio` - Create audio post

### **Comments**
- `POST /comments/posts/{post_id}` - Create comment
- `GET /comments/posts/{post_id}` - Get post comments
- `PUT /comments/{comment_id}` - Update comment
- `DELETE /comments/{comment_id}` - Delete comment
- `POST /comments/{comment_id}/approve` - Approve comment

### **Tags**
- `POST /tags/` - Create tag
- `GET /tags/` - List tags
- `GET /tags/popular` - Popular tags
- `PUT /tags/{tag_id}` - Update tag
- `DELETE /tags/{tag_id}` - Delete tag

### **Categories**
- `POST /categories/` - Create category
- `GET /categories/` - List categories
- `GET /categories/tree` - Category tree
- `GET /categories/popular` - Popular categories
- `PUT /categories/{category_id}` - Update category
- `DELETE /categories/{category_id}` - Delete category

### **Views**
- `POST /views/posts/{post_id}` - Record view
- `GET /views/posts/{post_id}/stats` - View statistics
- `GET /views/popular` - Popular posts

### **Uploads**
- `POST /uploads/multi` - Multi-file upload

### **SEO**
- `GET /sitemap.xml` - Generate sitemap

## Configuration

### **Environment Variables**
```env
DATABASE_URL=sqlite:///./blog.db
SECRET_KEY=your-secret-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_DATABASE_URL=your-supabase-db-url
REDIS_URL=redis://localhost:6379
SITE_BASE_URL=https://yoursite.com
```

### **Dependencies**
- FastAPI
- SQLAlchemy
- Redis
- Supabase
- Requests
- All dependencies listed in `requirements.txt`

## Usage Examples

### **Create Post with Excerpt**
```python
post_data = {
    "title": "My Blog Post",
    "body": "This is a long blog post with lots of content...",
    "clean": "my-blog-post",
    "excerpt": "Auto-generated excerpt..."  # Optional
}
```

### **Add Comment with MAPTCHA**
```python
# First get MAPTCHA challenge
challenge = requests.post("/maptcha/generate")

# Then create comment
comment_data = {
    "content": "Great post!",
    "maptcha_challenge_id": challenge["challenge_id"],
    "maptcha_answer": "42"
}
```

### **Process Content for Embeds**
```python
content = "Check out this video: https://youtube.com/watch?v=abc123"
processed = requests.post("/embed/process", json={"content": content})
```

## Performance Features

- **Redis Caching**: 5-minute and 1-hour cache durations
- **Connection Pooling**: PostgreSQL connection optimization
- **Cursor Pagination**: Efficient infinite scrolling
- **Lazy Loading**: Optimized database queries

## Security Features

- **JWT Authentication**: Secure user authentication
- **Permission System**: Role-based access control
- **MAPTCHA Protection**: Spam prevention
- **Input Validation**: Pydantic schema validation

## Next Steps

All backend features have been successfully implemented. The system is now ready for:

1. **Frontend Integration**: Connect React frontend to new APIs
2. **Testing**: Comprehensive API testing
3. **Deployment**: Production deployment setup
4. **Documentation**: Frontend integration guides

## Support

For questions or issues with the backend implementation, refer to:
- Individual router files for specific feature documentation
- `utils.py` for utility functions
- `models.py` for database schema
- `schemas.py` for data validation
