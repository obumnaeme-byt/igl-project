# Inter Global Logistic — Django Application

A production-ready logistics tracking platform built with Django 5, PostgreSQL, Redis, Celery, and Docker.

---

## 🏗️ Project Structure

```
igl_project/
├── igl_project/          # Django project config
│   ├── settings.py       # All settings (env-driven)
│   ├── urls.py           # Root URL routing
│   ├── wsgi.py           # WSGI entry point
│   └── celery.py         # Celery config
│
├── accounts/             # Custom User model + role system
├── core/                 # Public site (home, about, services, contact, track)
├── shipments/            # Shipment models, forms, API, PDF receipt generator
├── portal/               # Admin portal (login, dashboard, CRUD, status updates)
│
├── templates/
│   ├── base_public.html  # Public site base (navbar + footer)
│   ├── base_portal.html  # Admin portal base (sidebar layout)
│   ├── core/             # Public page templates
│   ├── portal/           # Admin portal templates
│   ├── receipts/         # PDF receipt HTML template
│   └── errors/           # 404 + 500 error pages
│
├── static/
│   ├── css/public.css    # Public site styles
│   ├── css/portal.css    # Admin portal styles
│   ├── js/public.js      # Public site JS (token formatter, counter)
│   └── js/portal.js      # Portal JS (sidebar, confirmations)
│
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── requirements.txt
└── .env.example
```

---

## ⚡ Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12+
- PostgreSQL 14+
- Redis 7+ (for caching & Celery)

### 2. Clone & set up virtual environment
```bash
git clone <your-repo-url> igl_project
cd igl_project
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, DB credentials, etc.
```

### 5. Create the PostgreSQL database
```bash
psql -U postgres
CREATE DATABASE igl_db;
CREATE USER igl_user WITH PASSWORD 'igl_password';
GRANT ALL PRIVILEGES ON DATABASE igl_db TO igl_user;
\q
```

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Create a superuser (Super Admin)
```bash
python manage.py createsuperuser
# Then in Django Admin (/django-admin/), set role to "super_admin"
# Or use shell: python manage.py shell
# >>> from accounts.models import User
# >>> u = User.objects.get(username='your_username')
# >>> u.role = 'super_admin'; u.is_staff = True; u.save()
```

### 8. Create a portal admin user
```bash
python manage.py shell
>>> from accounts.models import User
>>> User.objects.create_user(
...   username='admin',
...   email='admin@igl.com',
...   password='SecurePass2024!',
...   role='admin',
...   is_staff=True
... )
```

### 9. Collect static files
```bash
python manage.py collectstatic --noinput
```

### 10. Run the development server
```bash
python manage.py runserver
```

### 11. (Optional) Start Celery worker for async PDF generation
```bash
celery -A igl_project worker --loglevel=info
```

---

## 🌐 Application URLs

| URL | Description |
|-----|-------------|
| `/` | Homepage with tracking input |
| `/track/<TOKEN>/` | Public shipment tracking page |
| `/about/` | About page |
| `/services/` | Services page |
| `/contact/` | Contact form |
| `/portal/login/` | Admin portal login |
| `/portal/dashboard/` | Admin dashboard |
| `/portal/shipments/` | All shipments list |
| `/portal/shipments/new/` | Register new shipment |
| `/portal/shipments/<id>/` | Shipment detail + status update |
| `/portal/shipments/<id>/receipt/` | Download PDF receipt |
| `/api/v1/track/<TOKEN>/` | Public tracking REST API |
| `/django-admin/` | Super Admin panel |
| `/i18n/` | Language switcher |
| `/rosetta/` | Translation management UI |

---

## 🐳 Docker Deployment

### Build & run everything
```bash
cp .env.example .env
# Edit .env with production values: SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, etc.
docker-compose up --build -d
```

### Create superuser in Docker
```bash
docker-compose exec web python manage.py createsuperuser
```

### View logs
```bash
docker-compose logs -f web
docker-compose logs -f celery
```

### Stop
```bash
docker-compose down
```

---

## 🔐 Security Features

- **Login lockout**: 5 failed attempts → 15-minute lockout (django-axes)
- **Rate limiting**: Public API capped at 30 req/min per IP
- **CSRF protection**: All POST forms use `{% csrf_token %}`
- **Input validation**: Server-side form validation on all fields
- **Role-based access**: Admin vs Super Admin roles
- **Sensitive data masking**: Phone/address masked on public tracking page
- **Production security headers**: HSTS, XSS filter, content type nosniff

---

## 📦 Shipment Status Flow

```
REGISTERED → PICKED_UP → IN_TRANSIT → CUSTOMS → OUT_FOR_DELIVERY → DELIVERED
                                                                  ↘ FAILED_DELIVERY → RETURNED
                                        ↓
                                     ON_HOLD
```

Each status change creates an immutable **TrackingEvent** record visible on the public tracking page.

---

## 🧾 PDF Receipt

The receipt includes:
- Code128 barcode of the tracking token
- QR code linking to the public tracking page
- Sender & receiver details (full info for admin, masked for public)
- Package details, payment status
- Tracking history timeline
- Bilingual (EN/PT) footer

---

## 🌍 Internationalisation

10 languages supported: English, French, Spanish, Arabic, Portuguese, German, Chinese (Simplified), Hindi, Swahili, Russian.

To generate/update translation files:
```bash
python manage.py makemessages -l fr -l es -l ar -l pt -l de -l zh_hans -l hi -l sw -l ru
python manage.py compilemessages
```

Manage translations via Rosetta UI at `/rosetta/` (requires staff login).

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.0, DRF 3.15 |
| Database | PostgreSQL 16 |
| Cache / Sessions | Redis 7 + django-redis |
| Async Tasks | Celery 5 |
| PDF Generation | WeasyPrint 62 |
| Barcode | python-barcode |
| QR Code | qrcode[pil] |
| Login Security | django-axes |
| Translations | django-rosetta |
| Static Files | WhiteNoise |
| Deployment | Gunicorn + Nginx + Docker |
| Frontend | Bootstrap 5.3, Font Awesome 6, IBM Plex Sans, Syne |

