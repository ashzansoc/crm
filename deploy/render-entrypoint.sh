#!/bin/bash

set -e

cd /home/frappe/frappe-bench

# Configure DB BEFORE any bench commands that might try to connect
if [ -n "$DB_HOST" ]; then
    echo "db_host: $DB_HOST" >> sites/common_site_config.json.tmp
fi

if [ -n "$DB_PORT" ]; then
    echo "db_port: $DB_PORT" >> sites/common_site_config.json.tmp
fi

if [ -n "$DB_NAME" ]; then
    echo "db_name: $DB_NAME" >> sites/common_site_config.json.tmp
fi

# If we have temp config, merge it properly into JSON
if [ -f "sites/common_site_config.json.tmp" ]; then
    # Create proper JSON config
    cat > sites/common_site_config.json << EOF
{
  "socketio_port": 9000,
  "db_host": "${DB_HOST}",
  "db_port": ${DB_PORT:-5432},
  "db_name": "${DB_NAME:-frappe_crm}",
  "developer_mode": 0
}
EOF
    rm -f sites/common_site_config.json.tmp
fi

# Configure Redis
if [ -n "$REDIS_URL" ]; then
    bench set-config -g redis_cache $REDIS_URL
    bench set-config -g redis_queue $REDIS_URL
    bench set-config -g redis_socketio $REDIS_URL
fi

# Automatic Site Creation
SITE_NAME=${SITE_NAME:-"frontend"}

if [ ! -d "sites/$SITE_NAME" ]; then
    echo "Site $SITE_NAME does not exist. Attempting to create..."
    
    # Determine DB root password argument
    DB_ROOT_PASS_ARG=""
    if [ -n "$DB_ROOT_PASSWORD" ]; then
        DB_ROOT_PASS_ARG="--db-root-password $DB_ROOT_PASSWORD"
    fi

    # Determine DB root user argument (for Postgres)
    DB_ROOT_USER_ARG=""
    if [ -n "$DB_ROOT_USER" ]; then
        DB_ROOT_USER_ARG="--db-root-username $DB_ROOT_USER"
    fi

    # Determine DB Type (default to mariadb)
    DB_TYPE=${DB_TYPE:-mariadb}

    # Determine DB Host argument for new-site command
    # This is crucial for Postgres to avoid socket connection attempts
    DB_HOST_ARG=""
    if [ -n "$DB_HOST" ]; then
        DB_HOST_ARG="--db-host $DB_HOST"
    fi

    echo "Creating site with DB Type: $DB_TYPE"
    echo "DB Host: ${DB_HOST:-not set}"
    echo "DB Port: ${DB_PORT:-not set}"
    echo "DB Name: ${DB_NAME:-not set}"
    echo "DB Root User: ${DB_ROOT_USER:-not set}"
    echo "DB Root Password: ${DB_ROOT_PASSWORD:+***set***}"

    # For Postgres, we need to use the existing database name
    # The --db-name flag tells bench to use this existing database instead of creating a new one
    # Create the site
    # We use --force to overwrite if necessary
    # We temporarily disable exit on error to capture failure
    set +e
    
    if [ "$DB_TYPE" = "postgres" ]; then
        # For Postgres, use the existing database
        bench new-site "$SITE_NAME" \
            --db-type "$DB_TYPE" \
            $DB_HOST_ARG \
            --db-name "${DB_NAME:-frappe_crm}" \
            $DB_ROOT_USER_ARG \
            --admin-password "${ADMIN_PASSWORD:-admin}" \
            $DB_ROOT_PASS_ARG \
            --install-app crm \
            --force
    else
        # For MariaDB, let it create the database
        bench new-site "$SITE_NAME" \
            --db-type "$DB_TYPE" \
            $DB_HOST_ARG \
            $DB_ROOT_USER_ARG \
            --admin-password "${ADMIN_PASSWORD:-admin}" \
            $DB_ROOT_PASS_ARG \
            --install-app crm \
            --force
    fi
    
    EXIT_CODE=$?
    set -e

    if [ $EXIT_CODE -ne 0 ]; then
        echo "ERROR: bench new-site failed with exit code $EXIT_CODE"
        echo "Please check the logs above for database connection errors."
        exit $EXIT_CODE
    fi

    bench use "$SITE_NAME"
    
    # Enable scheduler
    bench --site "$SITE_NAME" enable-scheduler
else
    echo "Site $SITE_NAME already exists."
    bench use "$SITE_NAME"
fi

# Execute the command
exec "$@"
