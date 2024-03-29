#!/bin/bash

# Create swapspace
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# SSH deploy key setup
mkdir ~/.ssh/git-keys
curl https://gist.githubusercontent.com/vhermecz/4e2ae9468f2ff7532bf3f8155ac95c74/raw/f01b4b0c03d0b11dbbdc3967c7a566b2c6db17df/custom_keys_git_ssh --output ~/.ssh/custom_keys_git_ssh
chmod 700 ~/.ssh/custom_keys_git_ssh
echo "export GIT_SSH_COMMAND=~/.ssh/custom_keys_git_ssh" >> ~/.profile
source ~/.profile

# tbdrenzil - manually create ~/.ssh/git-keys/rappo-ai-landerbot-admin and ~/.ssh/git-keys/rappo-ai-landerbot-demo
chmod 600 ~/.ssh/git-keys/rappo-ai-landerbot-admin
chmod 600 ~/.ssh/git-keys/rappo-ai-landerbot-demo

# Clone git repos
cd ~
ssh -o "StrictHostKeyChecking no" github.com
git clone git@github.com:rappo-ai/landerbot-admin.git
chmod -R g+w ~/landerbot-admin
git clone git@github.com:rappo-ai/landerbot-demo.git
chmod -R g+w ~/landerbot-demo

# update credentials
# tbdrenzil - manually create ~/landerbot-admin/.env; Set RAPPO_ENV=prod, HOST_URL=https://admin.landerbot.rappo.ai, TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_USERNAME
# tbdrenzil - manually create ~/landerbot-admin/.deploy/nginx/.env from /landerbot-admin/.deploy/nginx/.env.template and update the env variables as needed
# tbdrenzil - [THIS MAY BE OPTIONAL AND COULD BE SKIPPED] manually create ~/landerbot-demo/.env from the template; no need to change or set anything as this bot uses the REST connector, not Telegram
# tbdrenzil - [OPTIONAL] manually add GCP service account json credentials to ~/landerbot-admin/.deploy/mgob/secrets/ and update bucket name in ~/landerbot-admin/.deploy/mgob/hourly.yml

# launch admin and demo docker containers first
cd ~/landerbot-admin
docker-compose --env-file ./.env -f docker-compose.base.yml -f docker-compose.yml up --build --force-recreate -d
cd ~/landerbot-demo
docker-compose --env-file ./.env -f docker-compose.base.yml -f docker-compose.yml up --build --force-recreate -d

# manually update your DNS entries - add A records for admin and client endpoints (confingured in nginx env) pointing to your server IP
# run .deploy/nginx/init-letsencrypt.sh after launching landerbot-admin and landerbot-demo as it has dependencies on networks created by these
# restart the admin container as the Telegram bot webhook needs to re-register once the nginx server and SSL certificate is up
