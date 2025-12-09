# FastAPI Project - Phase 0

## Project Structure

```
app/
  __init__.py
  main.py
  config.py
  
  db/
    session.py
    migrations/   # Alembic migrations
    
  models/
    base.py
    
  proxy/
    __init__.py
    
  admin/
    __init__.py
    
  core/
    __init__.py

templates/
static/
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit `.env` file with your database credentials:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_db
ADMIN_HOST=0.0.0.0
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SECRET_KEY=your-secret-key-change-in-production
```

### 3. Run Alembic Migrations

Initialize the database (first time only):

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

For subsequent migrations:

```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

### 4. Start the Server

Run with uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Or for production:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## API Endpoints

- **Health Check**: `GET /health` - Returns `{"status": "ok"}`
- **Root**: `GET /` - Returns welcome message

## Database

The project uses:
- SQLite as the database (via aiosqlite)
- SQLAlchemy 2.x with async support
- Alembic for migrations

### Database Models

Three main models are defined:

1. **Site** (`models/site.py`): Mirror domain configurations
   - `mirror_root`: Mirror domain (e.g., "mirror.com")
   - `source_root`: Source domain (e.g., "source.com")
   - Configuration options: proxy settings, ad control, media policy, etc.

2. **GlobalConfig** (`models/global_config.py`): Default configuration (single row)
   - Provides fallback values for all sites

3. **AdminUser** (`models/admin_user.py`): Database-stored admin accounts
   - For future use (main superadmin is env-based)

## Admin Authentication

### Env-Based Superadmin

The main admin account is configured via environment variables:
- `ADMIN_HOST`: Host where admin panel is accessible
- `ADMIN_USERNAME`: Admin username
- `ADMIN_PASSWORD`: Admin password (not hashed in env)
- `SECRET_KEY`: Used for signing session cookies

**Important**: The superadmin password is NOT stored in the database.

### Admin Routes

- **GET /login**: Login form
- **POST /login**: Process login credentials
- **GET /logout**: Logout and clear session
- **GET /admin**: Admin panel (requires authentication)

### Session Management

Sessions are managed using JWT tokens stored in httpOnly cookies:
- Cookie name: `admin_session`
- Expiration: 24 hours
- Signed with `SECRET_KEY`

## Configuration

All configuration is managed through Pydantic Settings in `app/config.py`, which reads from environment variables or `.env` file.

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test files:
```bash
pytest tests/test_url_mapping.py -v
pytest tests/test_admin_auth.py -v
```
