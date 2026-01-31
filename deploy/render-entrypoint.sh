#!/bin/bash

set -e

cd /home/frappe/frappe-bench

# Configure DB
if [ -n "$DB_HOST" ]; then
    bench set-config -g db_host $DB_HOST
fi

if [ -n "$DB_PORT" ]; then
    bench set-config -g db_port $DB_PORT
fi

# Configure Redis
if [ -n "$REDIS_URL" ]; then
    bench set-config -g redis_cache $REDIS_URL
    bench set-config -g redis_queue $REDIS_URL
    bench set-config -g redis_socketio $REDIS_URL
fi

# Set other configs
bench set-config -g developer_mode 0

# Automatic Site Creation
SITE_NAME=${SITE_NAME:-"frontend"}

if [ ! -d "sites/$SITE_NAME" ]; then
    echo "Site $SITE_NAME does not exist. Attempting to create..."
    
    # Determine DB root password argument
    DB_ROOT_PASS_ARG=""
    if [ -n "$DB_ROOT_PASSWORD" ]; then
        DB_ROOT_PASS_ARG="--db-root-password $DB_ROOT_PASSWORD"
    fi

    # Create the site
    # We use --force to overwrite if necessary, and --no-mariadb-socket to use TCP
    bench new-site "$SITE_NAME" \
        --no-mariadb-socket \
        --admin-password "${ADMIN_PASSWORD:-admin}" \
        $DB_ROOT_PASS_ARG \
        --install-app crm \
        --force

    bench use "$SITE_NAME"
    
    # Enable scheduler
    bench --site "$SITE_NAME" enable-scheduler
else
    echo "Site $SITE_NAME already exists."
    bench use "$SITE_NAME"
fi

# Execute the command
exec "$@"
