FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git build-essential pkg-config mariadb-client libmariadb-dev libpq-dev postgresql-client curl gnupg

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Install yarn
RUN npm install -g yarn

# Create user
RUN useradd -ms /bin/bash frappe

# Install bench
RUN pip install frappe-bench

# Switch to frappe user
USER frappe
WORKDIR /home/frappe

# Initialize bench
RUN bench init --skip-redis-config-generation --skip-assets --frappe-branch version-15 --python python3.11 frappe-bench

WORKDIR /home/frappe/frappe-bench

# Install postgres support
RUN ./env/bin/pip install psycopg2-binary

# Copy local app
COPY --chown=frappe:frappe . /home/frappe/frappe-bench/apps/crm

# Install app
RUN ./env/bin/pip install -e apps/crm
RUN echo "crm" >> sites/apps.txt

# Workaround for ModuleNotFoundError: No module named 'frappecrm'
RUN ln -s /home/frappe/frappe-bench/apps/crm/crm /home/frappe/frappe-bench/apps/crm/frappecrm

# Ensure common_site_config.json exists for frontend build
RUN echo '{"socketio_port": 9000}' > /home/frappe/frappe-bench/sites/common_site_config.json

# Build Frontend
WORKDIR /home/frappe/frappe-bench/apps/crm/frontend
RUN yarn install
RUN yarn build

# Switch back to bench
WORKDIR /home/frappe/frappe-bench

# Install frappe node dependencies explicitly
RUN cd apps/frappe && yarn install

# Build assets (only for frappe, since crm has no standard assets)
RUN bench build --app frappe

# Copy entrypoint
COPY --chown=frappe:frappe deploy/render-entrypoint.sh /usr/local/bin/render-entrypoint.sh
RUN chmod +x /usr/local/bin/render-entrypoint.sh

# Expose ports
EXPOSE 8000

ENTRYPOINT ["render-entrypoint.sh"]
CMD ["bench", "start"]
