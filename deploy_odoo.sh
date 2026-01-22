#!/bin/bash
set -e

IMAGE_NAME="odoo-custom:latest"
CONTAINER_NAME="odoo_prod"
NETWORK_NAME="private-net"

echo "===> Build Docker image"
docker build -t ${IMAGE_NAME} .

# Cek apakah network sudah ada, jika belum maka buat secara otomatis
if [ ! "$(docker network ls | grep ${NETWORK_NAME})" ]; then
  echo "===> Creating network ${NETWORK_NAME}..."
  docker network create ${NETWORK_NAME}
else
  echo "===> Network ${NETWORK_NAME} already exists."
fi

echo "===> Stop container (if exists)"
docker stop ${CONTAINER_NAME} 2>/dev/null || true

echo "===> Remove container (if exists)"
docker rm ${CONTAINER_NAME} 2>/dev/null || true

echo "===> Run new container"
docker run -d \
  --name ${CONTAINER_NAME} \
  --network ${NETWORK_NAME} \
  -p 9000:9000 \
  -p 8071:8071 \
  -v /srv/apps/odoo/Setup:/opt/odoo/Setup \
  -v /srv/apps/odoo/emm:/opt/odoo/emm \
  -v /srv/apps/odoo/odoo:/opt/odoo/odoo \
  -v /var/log/odoo:/var/log/odoo \
  --restart unless-stopped \
  ${IMAGE_NAME}

echo "===> Deployment finished successfully"
docker ps | grep ${CONTAINER_NAME}
