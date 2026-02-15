# Deployment & DevOps Reference

## Odoo.sh Deployment

### Branch Types

| Branch Type | Purpose | Database |
|-------------|---------|----------|
| Production | Live system | Persistent |
| Staging | Pre-production testing | Copy of production |
| Development | Feature development | Fresh or copy |

### odoo.sh Configuration

**.odoo.sh** file (optional):

```
[options]
; Submodules to include
submodules = True

; Custom commands to run
; pre-build = pip install special-package
```

### Build Triggers

- Push to any branch triggers build
- Production builds require manual merge
- Staging auto-syncs with production DB nightly (configurable)

### Custom Domains

```
# In Odoo.sh settings:
# - Add custom domain
# - Configure DNS CNAME to point to odoo.sh URL
# - SSL auto-provisioned via Let's Encrypt
```

## Docker Deployment

### docker-compose.yml

```yaml
version: "3.8"

services:
  odoo:
    image: odoo:18.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons
      - ./config/odoo.conf:/etc/odoo/odoo.conf:ro
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo_password
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=odoo_password
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - odoo-db-data:/var/lib/postgresql/data/pgdata
    restart: unless-stopped

volumes:
  odoo-web-data:
  odoo-db-data:
```

### Production docker-compose.yml

```yaml
version: "3.8"

services:
  odoo:
    image: odoo:18.0
    depends_on:
      - db
      - redis
    ports:
      - "127.0.0.1:8069:8069"
      - "127.0.0.1:8072:8072"  # Longpolling
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons:ro
      - ./config/odoo.conf:/etc/odoo/odoo.conf:ro
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=${POSTGRES_PASSWORD}
    restart: always
    deploy:
      resources:
        limits:
          memory: 4G

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - odoo-db-data:/var/lib/postgresql/data/pgdata
      - ./backup:/backup
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    image: redis:7-alpine
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - odoo
    restart: always

volumes:
  odoo-web-data:
  odoo-db-data:
```

### Dockerfile (Custom Image)

```dockerfile
FROM odoo:18.0

USER root

# Install additional system packages
RUN apt-get update && apt-get install -y \
    python3-dev \
    libldap2-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy custom addons
COPY --chown=odoo:odoo ./addons /mnt/extra-addons

USER odoo
```

## Server Configuration

### odoo.conf

```ini
[options]
; Database
db_host = localhost
db_port = 5432
db_user = odoo
db_password = secure_password
db_name = production_db
; db_template = template0
; db_maxconn = 64

; Paths
addons_path = /opt/odoo/addons,/opt/odoo/custom-addons
data_dir = /var/lib/odoo

; Server
http_port = 8069
longpolling_port = 8072
proxy_mode = True

; Workers (production)
workers = 4
max_cron_threads = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 600
limit_time_real = 1200
limit_time_real_cron = 3600
limit_request = 8192

; Logging
logfile = /var/log/odoo/odoo.log
log_level = info
; log_handler = :INFO,werkzeug:WARNING,odoo.addons.queue_job:DEBUG

; Security
admin_passwd = $pbkdf2-sha512$...  ; Hashed password
list_db = False
; dbfilter = ^production_db$

; Email
smtp_server = smtp.example.com
smtp_port = 587
smtp_user = odoo@example.com
smtp_password = email_password
smtp_ssl = False
email_from = odoo@example.com

; Performance
osv_memory_age_limit = 1.0
osv_memory_count_limit = False
unaccent = True
```

### Worker Calculation

```
# Formula for workers:
workers = (CPU cores * 2) + 1

# For 4 CPU cores:
workers = 4 * 2 + 1 = 9

# Memory per worker: ~150-300MB
# Total RAM needed: workers * 300MB + 2GB (base)

# Cron threads (separate from workers):
max_cron_threads = 2  # Usually 1-2 is enough
```

## Nginx Configuration

### nginx.conf

```nginx
upstream odoo {
    server 127.0.0.1:8069 weight=1 fail_timeout=0;
}

upstream odoo-chat {
    server 127.0.0.1:8072 weight=1 fail_timeout=0;
}

server {
    listen 80;
    server_name odoo.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name odoo.example.com;

    # SSL
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Logs
    access_log /var/log/nginx/odoo.access.log;
    error_log /var/log/nginx/odoo.error.log;

    # Proxy headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Timeouts
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;
    proxy_read_timeout 720s;

    # File upload size
    client_max_body_size 200m;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Longpolling
    location /longpolling {
        proxy_pass http://odoo-chat;
    }

    # Static files cache
    location ~* /web/static/ {
        proxy_pass http://odoo;
        proxy_cache_valid 200 90m;
        expires 90d;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        proxy_pass http://odoo;
        proxy_redirect off;
    }
}
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: odoo
          POSTGRES_PASSWORD: odoo
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage pytest-odoo

      - name: Run pre-commit
        run: |
          pip install pre-commit
          pre-commit run --all-files

      - name: Run tests
        run: |
          coverage run odoo-bin -c test.conf \
            -d test --test-enable \
            -i my_module --stop-after-init
          coverage report --fail-under=80
```

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-xml

  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        additional_dependencies:
          - flake8-bugbear

  - repo: https://github.com/OCA/pylint-odoo
    rev: v9.0.4
    hooks:
      - id: pylint_odoo
```

## Backup & Recovery

### Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"
DB_NAME="production"
FILESTORE="/var/lib/odoo/filestore/${DB_NAME}"

# Database dump
pg_dump -Fc -U odoo ${DB_NAME} > ${BACKUP_DIR}/db_${DATE}.dump

# Filestore backup
tar -czf ${BACKUP_DIR}/filestore_${DATE}.tar.gz -C ${FILESTORE} .

# Upload to S3 (optional)
aws s3 cp ${BACKUP_DIR}/db_${DATE}.dump s3://bucket/backups/
aws s3 cp ${BACKUP_DIR}/filestore_${DATE}.tar.gz s3://bucket/backups/

# Cleanup old backups (keep 7 days)
find ${BACKUP_DIR} -name "*.dump" -mtime +7 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +7 -delete
```

### Restore Script

```bash
#!/bin/bash
# restore.sh

DB_NAME="production"
BACKUP_FILE="db_20240115_120000.dump"
FILESTORE_BACKUP="filestore_20240115_120000.tar.gz"
FILESTORE="/var/lib/odoo/filestore/${DB_NAME}"

# Stop Odoo
systemctl stop odoo

# Drop and recreate database
dropdb -U odoo ${DB_NAME}
createdb -U odoo ${DB_NAME}

# Restore database
pg_restore -U odoo -d ${DB_NAME} ${BACKUP_FILE}

# Restore filestore
rm -rf ${FILESTORE}
mkdir -p ${FILESTORE}
tar -xzf ${FILESTORE_BACKUP} -C ${FILESTORE}
chown -R odoo:odoo ${FILESTORE}

# Start Odoo
systemctl start odoo
```

## Migration Between Versions

### Pre-Migration Checklist

1. **Backup everything**
2. **Test on copy first**
3. **Check module compatibility**
4. **Review breaking changes**
5. **Prepare migration scripts**

### Migration Steps

```bash
# 1. Create backup
./backup.sh

# 2. Stop Odoo
systemctl stop odoo

# 3. Update Odoo source
cd /opt/odoo
git fetch origin
git checkout 18.0

# 4. Update Python dependencies
pip install -r requirements.txt

# 5. Update custom addons
cd /opt/odoo/custom-addons
git pull origin 18.0

# 6. Run upgrade
./odoo-bin -c odoo.conf -d production -u all --stop-after-init

# 7. Verify and start
./odoo-bin -c odoo.conf -d production --test-enable --stop-after-init
systemctl start odoo
```

### OpenUpgrade (Major Version Migrations)

```bash
# Clone OpenUpgrade
git clone https://github.com/OCA/OpenUpgrade.git
cd OpenUpgrade
git checkout 18.0

# Run migration
./odoo-bin -c odoo.conf -d production \
    --update=all \
    --load=base,web,openupgrade_framework \
    --stop-after-init
```
