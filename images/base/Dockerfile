FROM node:24

ARG TZ
ENV TZ="$TZ"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 \
  python3-pip \
  python3-venv \
  less \
  git \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  jq \
  curl \
  nano \
  vim \
  ca-certificates \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Symlink python -> python3
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Ensure default node user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share

ARG USERNAME=node

# Persist bash/zsh history
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory \
  && echo "$SNIPPET" >> /home/$USERNAME/.bashrc

# Fix locale warnings
RUN apt-get update && apt-get install -y --no-install-recommends locales && \
  sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen && \
  apt-get clean && rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

ENV DEVCONTAINER=true

# Create workspaces and config dirs
RUN mkdir -p /workspaces /home/node/.claude && \
  chown -R node:node /workspaces /home/node/.claude

WORKDIR /workspaces

# Install git-delta for better diffs
ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# Switch to non-root user
USER node

# Set npm global prefix
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Default shell and editor
ENV SHELL=/bin/zsh
ENV EDITOR="code --wait"
ENV VISUAL="code --wait"

# Install zsh with powerlevel10k
ARG ZSH_IN_DOCKER_VERSION=1.2.0
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Install Playwright CLI globally
RUN npm install -g @playwright/cli@latest

# Install Chromium with OS-level dependencies
USER root
RUN cd /tmp && npx playwright-cli install --with-deps chromium
USER node

# Install Claude Code via native installer
COPY --chown=node:node assets/claude-install.sh /tmp/claude-install.sh
RUN bash /tmp/claude-install.sh && rm /tmp/claude-install.sh && \
  cp /home/node/.local/bin/claude /usr/local/share/npm-global/bin/claude

# Disable line ending conversion (Windows host adds \r\n otherwise)
RUN git config --global core.autocrlf false

# Copy statusline script
COPY --chown=node:node assets/statusline.sh /usr/local/bin/claude-statusline.sh
RUN chmod +x /usr/local/bin/claude-statusline.sh

# Copy startup script
COPY --chown=node:node assets/start.sh /usr/local/bin/devcontainer-start.sh
RUN chmod +x /usr/local/bin/devcontainer-start.sh
