# rasa-bot-template
Rasa Bot Template source code repository.

# Build steps

## Environment Variables

Copy .env.template to .env and set at-least the mandatory environment variables below.

- MGOB_EXTERNAL_PORT - mongo db backup container external port; not used for devcontainer; defaults to 8090 [REQUIRED]
- MONGO_EXPRESS_EXTERNAL_PORT - mongo express container external port; defaults to 8081 [REQUIRED]
- RASA_EXTERNAL_DEBUG_PORT - rasa server external port; used only in devcontainer; defaults to 5005 [REQUIRED]
- TELEGRAM_BOT_TOKEN - Telegram bot token [OPTIONAL]
- TELEGRAM_BOT_USERNAME - Telegram bot username [OPTIONAL]
- NGROK_AUTH_TOKEN - Ngrok auth token [OPTIONAL]
- NGROK_REGION - Ngrok region [OPTIONAL]
- RAPPO_ENV - Defaults to debug [OPTIONAL]
- HOST_URL - If set, HOST_URL is used instead of ngrok [OPTIONAL]

Contact repo owner for help with 3rd party credentials.

## Launch without debugging (Production)

### Docker Compose with Linux engine
```bash
docker-compose -f docker-compose.base.yml -f docker-compose.yml up --build -d
```

## Launch with debugging (Local)

Install VS Code with Remote-Containers extension. (https://code.visualstudio.com/download)

### Windows devcontainer setup
- Install WSL 2 (Windows Subsystem for Linux) first along with a Linux distribution (such as Ubuntu 20.04) (https://docs.microsoft.com/en-us/windows/wsl/install-win10)
- Install Docker Desktop and configure it to use WSL (see instructions on https://www.docker.com/)
- Set your git email, password, credentials, etc. in the WSL Linux OS so that devcontainer can pick these credentials up later. (https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup)
- Clone this repository inside WSL Linux filesystem for performance reasons with Docker (see https://docs.docker.com/docker-for-windows/wsl/#develop-with-docker-and-wsl-2)
- Change the usergroup of all source code files to 'root' to grant the Docker container user the appropriate permissions (you do not need to set file permissions to 770, so just use the chgrp command from this link https://rasa.com/docs/rasa-x/installation-and-setup/install/docker-compose/#permissions-on-mounted-directories)
- Open repository inside WSL Linux with VS Code. Launch as devcontainer when prompted. (see https://docs.docker.com/docker-for-windows/wsl/#develop-with-docker-and-wsl-2)

### OSX devcontainer setup
- Install Docker Desktop (see instructions on https://www.docker.com/)
- Clone this repository and open it with VS Code. Launch as devcontainer when prompted.

### Linux devcontainer setup
- Install Docker Desktop (see instructions on https://www.docker.com/)
- Clone this repository.
- Change the usergroup of all source code files to 'root' to grant the Docker container user the appropriate permissions (you do not need to set file permissions to 770, so just use the chgrp command from this link https://rasa.com/docs/rasa-x/installation-and-setup/install/docker-compose/#permissions-on-mounted-directories)
- Open repository with VS Code. Launch as devcontainer when prompted.

### Launch Rasa server
In VSCode 'Run and Debug' tab, select 'rasa run' and click Start Debugging.

Note:
- The actions server does not launch automatically with the rasa server. You need to manually start the action server as well. Your bot will still work but actions will not execute.
- To debug incoming messages from Telegram to Rasa, you can set a breakpoint in "dataset/connectors/telegram.py" under the server route "/webhook".

### Launch Rasa actions server
In VSCode 'Run and Debug' tab, select 'rasa run actions' and click Start Debugging.

Note:
- To debug action code, just set a breakpoint in the corresponding action file inside "dataset/actions".
