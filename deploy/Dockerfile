FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git build-essential pkg-config mariadb-client libmariadb-dev libpq-dev postgresql-client curl gnupg libyaml-dev python3-dev libffi-dev libssl-dev cron

# Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install yarn
RUN npm install -g yarn@1.22.19
RUN yarn config set network-timeout 1000000
RUN yarn config set unsafe-perm true
RUN yarn config set network-concurrency 1

# Set Node options for memory
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Create user
RUN useradd -ms /bin/bash frappe

# Install bench
RUN pip install --upgrade pip && pip install frappe-bench

# Switch to frappe user
USER frappe
WORKDIR /home/frappe

# Fix SSL issue for MariaDB client
RUN echo "[client]" > /home/frappe/.my.cnf && \
    echo "ssl=0" >> /home/frappe/.my.cnf

# Configure git
RUN git config --global user.email "frappe@example.com" && git config --global user.name "Frappe User"
RUN git config --global http.postBuffer 524288000

# Initialize bench
RUN bench init --verbose --skip-redis-config-generation --skip-assets --frappe-branch version-15 --python python3 frappe-bench || (cat /home/frappe/frappe-bench/logs/bench.log && exit 1)

WORKDIR /home/frappe/frappe-bench

# Install postgres support
RUN ./env/bin/pip install psycopg2-binary

# Ensure common_site_config.json exists (needed for bench build sometimes)
RUN echo '{"socketio_port": 9000}' > /home/frappe/frappe-bench/sites/common_site_config.json

# Build Frappe Assets (moved up to isolate failure and ensure base is ready)
RUN cd apps/frappe && yarn install
RUN bench build --app frappe --force

# Copy local app
COPY --chown=frappe:frappe . /home/frappe/frappe-bench/apps/crm

# Install app
RUN ./env/bin/pip install -e apps/crm
RUN echo "frappe" > sites/apps.txt && echo "crm" >> sites/apps.txt

# Workaround for ModuleNotFoundError: No module named 'frappecrm'
# The app name is 'crm' but sometimes it might be referred to as 'frappecrm' in some contexts or imports
# We create a symlink to ensure it can be found if imported as 'frappecrm'
RUN ln -s /home/frappe/frappe-bench/apps/crm/crm /home/frappe/frappe-bench/apps/crm/frappecrm

# Build Frontend
WORKDIR /home/frappe/frappe-bench/apps/crm/frontend
RUN yarn install
RUN yarn build

# Switch back to bench
WORKDIR /home/frappe/frappe-bench

# Build assets for crm app
RUN bench build --app crm --force

# Cache assets to avoid volume masking issues
RUN mkdir -p /home/frappe/assets_cache && \
    cp -R /home/frappe/frappe-bench/sites/assets/* /home/frappe/assets_cache/

# Copy entrypoint
USER root
COPY deploy/render-entrypoint.sh /usr/local/bin/render-entrypoint.sh
RUN chmod +x /usr/local/bin/render-entrypoint.sh
RUN chown frappe:frappe /usr/local/bin/render-entrypoint.sh
# Fix line endings just in case
RUN sed -i 's/\r$//' /usr/local/bin/render-entrypoint.sh

# Switch back to frappe user
USER frappe

# Expose ports
EXPOSE 8000

ENTRYPOINT ["render-entrypoint.sh"]
CMD ["bench", "start"]
