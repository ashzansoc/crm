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
bench set-config -g serve_default_site 1
bench set-config -g restart_supervisor_on_update 0
bench set-config -g restart_systemd_on_update 0

# Restore assets from cache (to handle volume masking)
if [ -d "/home/frappe/assets_cache" ]; then
    echo "Restoring assets from cache..."
    cp -R /home/frappe/assets_cache/* /home/frappe/frappe-bench/sites/assets/
fi

# Ensure apps.txt is correct (to handle volume persistence of old bad config)
echo "frappe" > sites/apps.txt && echo "crm" >> sites/apps.txt

# Automatic Site Creation
SITE_NAME=${SITE_NAME:-"frontend"}

if [ ! -d "sites/$SITE_NAME" ]; then
    echo "Site $SITE_NAME does not exist. Attempting to create..."
    
    # Determine DB root password argument
    DB_ROOT_PASS_ARG=""
    if [ -n "$DB_ROOT_PASSWORD" ]; then
        DB_ROOT_PASS_ARG="--db-root-password $DB_ROOT_PASSWORD"
    fi

    # Determine DB Type (default to mariadb)
    DB_TYPE=${DB_TYPE:-mariadb}

    # Determine DB Host argument for new-site command
    DB_HOST_ARG=""
    if [ -n "$DB_HOST" ]; then
        DB_HOST_ARG="--db-host $DB_HOST"
    fi

    echo "Creating site with DB Type: $DB_TYPE"

    # Create the site
    # We use --force to overwrite if necessary
    # We temporarily disable exit on error to capture failure
    set +e
    
    # For Postgres, we need to specify the maintenance database if it's not 'postgres' or 'template1'
    # But usually 'postgres' exists. The error 'database "frappe" does not exist' suggests
    # bench is trying to connect to a db named 'frappe' by default or derived from user.
    # We will try to force the root login to use the 'postgres' database for initial connection.
    
    bench new-site "$SITE_NAME" \
        --db-type "$DB_TYPE" \
        $DB_HOST_ARG \
        --admin-password "${ADMIN_PASSWORD:-admin}" \
        $DB_ROOT_PASS_ARG \
        --install-app crm \
        --force
    
    EXIT_CODE=$?
    set -e

    if [ $EXIT_CODE -ne 0 ]; then
        echo "ERROR: bench new-site failed with exit code $EXIT_CODE"
        echo "Please check the logs above for database connection errors."
        exit $EXIT_CODE
    fi

    bench use "$SITE_NAME"
    
    # Clear cache and rebuild assets to ensure they're properly linked
    echo "Clearing cache and ensuring assets are available..."
    bench --site "$SITE_NAME" clear-cache
    bench --site "$SITE_NAME" build
    
    # Enable scheduler
    bench --site "$SITE_NAME" enable-scheduler
else
    echo "Site $SITE_NAME already exists."
    bench use "$SITE_NAME"
    
    # Ensure assets are available
    echo "Ensuring assets are available..."
    bench --site "$SITE_NAME" clear-cache
    bench --site "$SITE_NAME" build
fi

# Execute the command
exec "$@"
