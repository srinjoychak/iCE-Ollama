#!/bin/bash
ip_address=$(hostname -I | awk '{print $1}')
. ./.env
new_entry="$ip_address ollamaservice.com"
sudo sed -i '/ollamaservice.com/d' /etc/hosts
# echo "$new_entry" | sudo tee -a /etc/hosts
compose_file="docker-compose.yml"
sed -i "s/<ip_address>/$ip_address/g" "$compose_file"
docker rm -f streamlit_test django_test

docker rmi ice_django_image_test:latest ice_stremlit_image_test:latest

# Start containers using docker-compose
docker-compose build
docker run -d -p 5120:8501 --name  streamlit_test ice_stremlit_image_test:latest
docker run -d -p 5121:8200 --name  django_test ice_django_image_test:latest 