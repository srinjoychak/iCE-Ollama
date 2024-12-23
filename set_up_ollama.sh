#!/bin/bash
ip_address=$(hostname -I | awk '{print $1}')
. ./.env
new_entry="$ip_address ollamaservice.com"
sudo sed -i '/ollamaservice.com/d' /etc/hosts
# echo "$new_entry" | sudo tee -a /etc/hosts
compose_file="docker-compose.yml"
sed -i "s/<ip_address>/$ip_address/g" "$compose_file"
docker rm -f streamlit_ollama django_ollama ollama


docker rmi ice_scrumbot_ollama_ice_webex:latest ice_scrumbot_ollama_django:latest

# Start containers using docker-compose
docker-compose up --build -d


echo "Waiting for containers to initialize..."
sleep 30


expect << EOF
    spawn docker exec -it ollama ollama run $MODEL_NAME
    expect ">>> Send a message (/? for help)"
    send "/bye\r"
    expect eof
EOF