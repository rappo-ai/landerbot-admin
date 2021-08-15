#!/bin/bash

# Create swapspace
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# SSH deploy key setup
# tbdrenzil - manually create ~/.ssh/id_gitdeploykey
chmod 600 ~/.ssh/id_gitdeploykey
eval "$(ssh-agent -s)"
touch ~/.ssh/config
echo "Host *
  AddKeysToAgent yes
  IdentityFile ~/.ssh/id_gitdeploykey
" >> ~/.ssh/config
ssh-add ~/.ssh/id_gitdeploykey

# Clone git repo
cd ~
ssh -o "StrictHostKeyChecking no" github.com
git clone git@github.com:rappo-ai/rasa-bot-template.git
chmod -R g+w ~/rasa-bot-template

# update credentials
# tbdrenzil - manually create ~/rasa-bot-template/.env
# tbdrenzil - [OPTIONAL] manually create create ~/rasa-bot-template/.deploy/nginx/.env from /rasa-bot-template/.deploy/nginx/.env.template and update the env variables as needed
# tbdrenzil - [OPTIONAL] manually add GCP service account json credentials to ~/rasa-bot-template/.deploy/mgob/secrets/ and update bucket name in ~/rasa-bot-template/.deploy/mgob/hourly.yml

# launch docker
cd ~/rasa-bot-template
docker-compose -f docker-compose.base.yml -f docker-compose.yml up --build --force-recreate -d
