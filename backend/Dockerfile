FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    curl \
    byobu \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ARG HOST_UID=1000
ARG HOST_GID=1000
RUN groupmod -g ${HOST_GID} ubuntu && \
    usermod -u ${HOST_UID} -g ${HOST_GID} ubuntu && \
    mkdir -p /app && \
    chown -R ubuntu:ubuntu /app /home/ubuntu

USER ubuntu
WORKDIR /app

COPY --chown=ubuntu:ubuntu package.json package-lock.json ./
RUN npm ci

COPY --chown=ubuntu:ubuntu . .

EXPOSE 3000

CMD ["bash"]
