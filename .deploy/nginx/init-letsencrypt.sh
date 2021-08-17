#!/bin/bash

if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Error: docker-compose is not installed.' >&2
  exit 1
fi

if [ -f ./.env ]; then
  source ./.env
else
  echo "No .env file found, using defaults."
fi


domains_env="${NGINX_DOMAIN_LIST:-"admin.landerbot.rappo.ai client.landerbot.rappo.ai"}"
IFS=' ' read -r -a domains <<< "$domains_env"
primary_domain=${domains[0]:-$NGINX_PRIMARY_DOMAIN}
rsa_key_size=4096
data_path="./data/certbot"
email=${LETSENCRYPT_EMAIL:-"support@rappo.ai"} # Adding a valid address is strongly recommended
staging=${LETSENCRYPT_STAGING:-0} # Set to 1 if you're testing your setup to avoid hitting request limits
admin_proxy_pass=${NGINX_ADMIN_PROXY_PASS:-"http://rasa-admin:5005"}
client_proxy_pass=${NGINX_CLIENT_PROXY_PASS:-"http://rasa-client:5005"}
escaped_admin_proxy_pass=$(printf '%s\n' "$admin_proxy_pass" | sed -e 's/[\/&]/\\&/g')
escaped_client_proxy_pass=$(printf '%s\n' "$client_proxy_pass" | sed -e 's/[\/&]/\\&/g')
admin_domain=${NGINX_ADMIN_DOMAIN:-"admin.landerbot.rappo.ai"}
client_domain=${NGINX_CLIENT_DOMAIN:-"client.landerbot.rappo.ai"}
allowed_client_origins=${ALLOWED_CLIENT_ORIGINS:-"https://landerbot.rappo.ai"}
escaped_allowed_client_origins=$(printf '%s\n' "$allowed_client_origins" | sed -e 's/[\/&]/\\&/g')

echo "### Creating nginx app.conf from template ..."
sed "s/\${NGINX_DOMAIN_LIST}/${domains_env}/g; s/\${NGINX_PRIMARY_DOMAIN}/${primary_domain}/g; s/\${NGINX_ADMIN_PROXY_PASS}/${escaped_admin_proxy_pass}/g; s/\${NGINX_CLIENT_PROXY_PASS}/${escaped_client_proxy_pass}/g; s/\${NGINX_ADMIN_DOMAIN}/${admin_domain}/g; s/\${NGINX_CLIENT_DOMAIN}/${client_domain}/g; s/\${ALLOWED_CLIENT_ORIGINS}/${escaped_allowed_client_origins}/g" ./templates/nginx/app.conf.template > ./data/nginx/app.conf
echo

if [ -d "$data_path" ]; then
  read -p "Existing data found for $domains. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi


if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

echo "### Creating dummy certificate for $domains ..."
path="/etc/letsencrypt/live/$domains"
mkdir -p "$data_path/conf/live/$domains"
docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo


echo "### Starting nginx ..."
docker-compose up --force-recreate -d nginx
echo

echo "### Deleting dummy certificate for $domains ..."
docker-compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domains && \
  rm -Rf /etc/letsencrypt/archive/$domains && \
  rm -Rf /etc/letsencrypt/renewal/$domains.conf" certbot
echo


echo "### Requesting Let's Encrypt certificate for $domains ..."
#Join $domains to -d args
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Select appropriate email arg
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# Enable staging mode if needed
if [ $staging != "0" ]; then staging_arg="--staging"; fi

docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

echo "### Reloading nginx ..."
docker-compose exec nginx nginx -s reload
