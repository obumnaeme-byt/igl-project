#!/usr/bin/env bash
set -o errexit

apt-get update && apt-get install -y --no-install-recommends \
  libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
  libcairo2 libxml2 libxslt1.1 libffi-dev

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate