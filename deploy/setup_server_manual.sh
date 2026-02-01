#!/bin/bash

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Install Docker Compose (if not included in docker installation)
sudo apt-get update
sudo apt-get install -y docker-compose-plugin

# Create directory for app
mkdir -p ~/crm

echo "Setup complete. Please log out and log back in for group changes to take effect."
