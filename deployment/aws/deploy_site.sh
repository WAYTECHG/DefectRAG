#!/bin/bash
# Build the static showcase and copy it to the Lightsail server.
# Run from the project root in Git Bash:
#   export WEB_HOST=<static IP>  WEB_KEY=<path to .pem>  [STATUS_URL=<Lambda function URL>]
#   bash deployment/aws/deploy_site.sh
set -euo pipefail

: "${WEB_HOST:?Set WEB_HOST to the Lightsail static IP or domain}"
: "${WEB_KEY:?Set WEB_KEY to the path of the SSH private key}"
USER_NAME="${WEB_USER:-ubuntu}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

echo "1/4 Building the static showcase..."
( cd "$ROOT/frontend" && npm ci && npm run build:showcase )

echo "2/4 Preparing files..."
cp -r "$ROOT/frontend/dist-static/." "$STAGE/"
sed "s#__STATUS_URL__#${STATUS_URL:-}#g" "$ROOT/deployment/aws/site/status.html" > "$STAGE/status.html"
[ -f "$STAGE/index.html" ] || { echo "index.html missing. Build failed?"; exit 1; }
tar -C "$STAGE" -czf "$STAGE/site.tgz" --exclude=site.tgz .

echo "3/4 Uploading to $WEB_HOST ..."
scp -i "$WEB_KEY" -o StrictHostKeyChecking=accept-new "$STAGE/site.tgz" "$USER_NAME@$WEB_HOST:/tmp/site.tgz"

echo "4/4 Switching the live site..."
ssh -i "$WEB_KEY" "$USER_NAME@$WEB_HOST" '
  set -e
  NEW=$(mktemp -d /var/www/defectrag-new.XXXXXX)
  tar -xzf /tmp/site.tgz -C "$NEW" && rm -f /tmp/site.tgz
  sudo rm -rf /var/www/defectrag-old
  [ -d /var/www/defectrag ] && sudo mv /var/www/defectrag /var/www/defectrag-old
  sudo mv "$NEW" /var/www/defectrag
  sudo chown -R www-data:www-data /var/www/defectrag
  sudo chmod 755 /var/www/defectrag
  sudo nginx -t && sudo systemctl reload nginx
'
echo "Done. Open http://$WEB_HOST"
