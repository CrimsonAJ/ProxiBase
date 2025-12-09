# ProxiBase Phase 3 - Demo Guide

## Quick Start

### 1. Access the Admin Panel

**Login Page**: `http://0.0.0.0:8001/login`

**Credentials**:
- Username: `admin`
- Password: `admin123`

### 2. Features to Try

#### Dashboard (`/admin`)
- View system statistics
- Total sites count
- Active sites count
- Quick action buttons

#### Sites Management (`/admin/sites`)

**View Sites**:
- See all configured proxy sites
- Status badges (Active/Disabled)
- Quick edit and delete actions

**Create New Site** (`/admin/sites/create`):
1. Click "Create New Site" button
2. Fill in required fields:
   - Mirror Root: `mirror.example.com`
   - Source Root: `source.example.com`
3. Optionally configure:
   - Proxy settings (subdomains, external domains)
   - Content modification (remove/inject ads, analytics)
   - Media policy and session mode
4. Click "Create Site"

**Edit Site** (`/admin/sites/{id}/edit`):
1. Click "Edit" button on any site
2. Modify configuration
3. Save changes

**Delete Site**:
1. Click "Delete" button
2. Confirm deletion

#### Global Settings (`/admin/settings`)

Configure default settings for all sites:

**Proxy Defaults**:
- ✅ Proxy Subdomains
- ✅ Proxy External Domains
- ⬜ Rewrite JS Redirects

**Content Modification**:
- ⬜ Remove Ads
- ⬜ Inject Custom Ads
- ⬜ Remove Analytics
- Custom Ad HTML (textarea)
- Custom Tracker JavaScript (textarea)

**Advanced Configuration**:
- Media Policy: Bypass / Proxy / Size Limited
- Session Mode: Stateless / Cookie Jar

### 3. Theme Toggle

- Click the 🌙/☀️ button in the header
- Theme preference is saved automatically
- Works on all pages including login

### 4. Navigation

**Header Menu**:
- Dashboard - View stats and quick actions
- Sites - Manage proxy sites
- Settings - Configure global defaults

**User Section**:
- User badge shows logged-in username and role
- Logout button to end session

## UI Features Showcase

### Modern Design Elements

1. **Gradient Accents**:
   - Buttons use indigo-to-purple gradient
   - Logo has gradient text effect
   - Login page background gradient

2. **Interactive Elements**:
   - Hover effects on all buttons
   - Smooth transitions
   - Card elevation on hover
   - Status badges with color coding

3. **Form Design**:
   - Checkbox items with background
   - Radio buttons with visual feedback
   - Textarea for code input (monospace font)
   - Inline form help text
   - Validation feedback

4. **Table Design**:
   - Hover effects on rows
   - Clean borders and spacing
   - Code-style display for domains
   - Action buttons grouped

5. **Empty States**:
   - Friendly messages when no data
   - Large emoji icons
   - Helpful call-to-action text

### Dark Mode vs Light Mode

**Light Mode**:
- Clean white backgrounds
- Subtle shadows
- Clear text contrast

**Dark Mode**:
- Deep blue-gray backgrounds
- Reduced eye strain
- Elegant appearance
- Proper contrast maintained

## Configuration Examples

### Example 1: Basic Proxy Site
```
Mirror Root: proxy.mysite.com
Source Root: original.com
Enabled: ✅
All other settings: Use Global Defaults
```

### Example 2: Ad-Free Mirror
```
Mirror Root: clean.mysite.com
Source Root: ads-heavy-site.com
Enabled: ✅
Remove Ads: ✅
Remove Analytics: ✅
Media Policy: Proxy
```

### Example 3: Custom Tracking Mirror
```
Mirror Root: tracked.mysite.com
Source Root: external-site.com
Enabled: ✅
Inject Ads: ✅
Custom Ad HTML: <div class="custom-ad">...</div>
Custom Tracker JS: // Google Analytics code
Session Mode: Cookie Jar
```

## API Endpoints (for testing)

### Authentication
```bash
# Login
POST /login
Content-Type: application/x-www-form-urlencoded
Host: 0.0.0.0

username=admin&password=admin123
```

### Sites Management
```bash
# List all sites
GET /admin/sites
Cookie: admin_session={token}
Host: 0.0.0.0

# Create site
POST /admin/sites/create
Cookie: admin_session={token}
Host: 0.0.0.0
Content-Type: application/x-www-form-urlencoded

mirror_root=test.com&source_root=source.com&enabled=true

# Edit site
POST /admin/sites/1/edit
Cookie: admin_session={token}
Host: 0.0.0.0
Content-Type: application/x-www-form-urlencoded

mirror_root=test.com&source_root=updated.com&enabled=true

# Delete site
POST /admin/sites/1/delete
Cookie: admin_session={token}
Host: 0.0.0.0
```

### Global Settings
```bash
# View settings
GET /admin/settings
Cookie: admin_session={token}
Host: 0.0.0.0

# Update settings
POST /admin/settings
Cookie: admin_session={token}
Host: 0.0.0.0
Content-Type: application/x-www-form-urlencoded

proxy_subdomains=true&remove_ads=false&media_policy=proxy&session_mode=stateless
```

## Tips

1. **Theme Toggle**: Your preference is saved in browser localStorage
2. **Form Validation**: Required fields are marked with *
3. **Checkboxes**: Leave unchecked to use global defaults
4. **Empty Values**: Use empty select options to inherit global config
5. **Session**: Lasts 24 hours, then requires re-login
6. **Host Security**: Admin panel only accessible from configured ADMIN_HOST

## Troubleshooting

### Cannot Access Admin Panel
- Check ADMIN_HOST setting in `.env`
- Ensure Host header matches ADMIN_HOST
- Verify backend is running: `sudo supervisorctl status backend`

### Login Failed
- Check credentials in `.env` file:
  - ADMIN_USERNAME=admin
  - ADMIN_PASSWORD=admin123

### Changes Not Saving
- Check browser console for errors
- Verify database permissions
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`

### Theme Not Persisting
- Check browser localStorage is enabled
- Try different browser
- Clear cache and reload

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy (async)
- **Database**: SQLite (with aiosqlite)
- **Templates**: Jinja2
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Styling**: Custom CSS with CSS Variables
- **Font**: Inter (Google Fonts)
