#!/bin/bash
# Lightsail "launch script" for Ubuntu 24.04. Installs nginx and prepares the web folder.
# Runs once as root at first boot. Safe to re-run.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx unattended-upgrades

mkdir -p /var/www/defectrag
echo '<h1>DefectRAG: server ready. Publish the site with deploy_site.sh.</h1>' > /var/www/defectrag/index.html
chown -R ubuntu:ubuntu /var/www/defectrag

cat > /etc/nginx/sites-available/defectrag <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    root /var/www/defectrag;
    index index.html;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    # Hashed build files never change, so they can be cached for a year.
    location /assets/ {
        add_header Cache-Control "public, max-age=31536000, immutable";
        try_files $uri =404;
    }

    # These can change between deploys: always re-check them.
    location = /config.js            { add_header Cache-Control "no-cache"; }
    location = /showcase/data.json   { add_header Cache-Control "no-cache"; }
    location = /index.html           { add_header Cache-Control "no-cache"; }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/defectrag /etc/nginx/sites-enabled/defectrag
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable --now nginx
systemctl reload nginx
