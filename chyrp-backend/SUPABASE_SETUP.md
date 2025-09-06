# Supabase PostgreSQL Setup Guide

## Environment Variables Required

Create a `.env` file in the backend directory with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google AI Configuration
GOOGLE_API_KEY=your-google-ai-api-key

# Redis Configuration (Optional - for caching)
REDIS_URL=redis://localhost:6379
```

## How to Get Supabase Database URL

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **Database**
3. Scroll down to **Connection string**
4. Select **URI** and copy the connection string
5. Replace `[YOUR-PASSWORD]` with your actual database password
6. Replace `[YOUR-PROJECT-REF]` with your project reference

Example:
```
postgresql://postgres:yourpassword@db.abcdefghijklmnop.supabase.co:5432/postgres
```

## Benefits of Using Supabase PostgreSQL

- ✅ **Unified Platform**: Database and file storage in one place
- ✅ **Real-time Features**: Built-in real-time subscriptions
- ✅ **Automatic Backups**: Managed database backups
- ✅ **Scalability**: Auto-scaling database
- ✅ **Security**: Built-in Row Level Security (RLS)
- ✅ **Monitoring**: Built-in database monitoring and logs


