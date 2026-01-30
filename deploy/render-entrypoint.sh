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

# Execute the command
exec "$@"
