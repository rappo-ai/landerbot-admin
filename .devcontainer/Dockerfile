FROM rappoai/rasa:telegram-2f575bf

USER root

RUN apt-get update && \
    curl -sL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y --no-install-recommends \
    sudo \
    ssh \
    git \
    nodejs && \
    . /opt/venv/bin/activate && \
    npm i -g ngrok --unsafe-perm=true && \
    pip install black && \
    pip install python-dotenv

WORKDIR /app/dataset

USER 1001
