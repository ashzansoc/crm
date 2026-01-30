#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
ZONE="us-central1-a"
VM_NAME="crm-server"

echo "=========================================="
echo "Continuing Deployment to GCP"
echo "Project: $PROJECT_ID"
echo "VM Name: $VM_NAME"
echo "Zone:    $ZONE"
echo "=========================================="

# 3. Prepare and Copy Files
echo "Packaging application..."
# Go to project root (assuming script is in crm/deploy/)
cd "$(dirname "$0")/../.."
# Tar the crm directory, excluding heavy/unnecessary files
tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='frappe-bench' \
    --exclude='*.tar.gz' \
    -czf crm-deploy.tar.gz crm

echo "Uploading application to VM..."
gcloud compute scp crm-deploy.tar.gz ubuntu@$VM_NAME:~ --zone=$ZONE --project=$PROJECT_ID

# 4. Deploy on VM
echo "Building and starting containers on VM..."
gcloud compute ssh ubuntu@$VM_NAME --zone=$ZONE --project=$PROJECT_ID --command='
# Extract
tar -xzf crm-deploy.tar.gz
cd crm

# Wait for Docker to be ready
while ! docker system info > /dev/null 2>&1; do
  echo "Waiting for Docker to start..."
  sleep 5
done

# Run Docker Compose
sudo docker compose -f deploy/docker-compose.prod.yml up -d --build
'

# 5. Get IP
IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "=========================================="
echo "Deployment Complete!"
echo "Your CRM is accessible at: http://$IP"
echo "=========================================="
echo "Note: It might take a few minutes for the site to be fully ready after the container starts."
