#!/usr/bin/env bash
set -euo pipefail

echo "=== Updating system ==="
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# -----------------------------
# Install Docker
# -----------------------------
if ! command -v docker >/dev/null 2>&1; then
  echo "=== Installing Docker ==="

  sudo install -m 0755 -d /etc/apt/keyrings

  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  echo "=== Enabling Docker ==="
  sudo systemctl enable docker
  sudo systemctl start docker

  echo "=== Adding user to docker group ==="
  sudo groupadd -f docker
  sudo usermod -aG docker "$USER"

newgrp docker
else
  echo "Docker already installed, skipping."
fi

# -----------------------------
# Install uv (Python)
# -----------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "=== Installing uv ==="
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Ensure uv is on PATH for this session
  export PATH="$HOME/.cargo/bin:$PATH"
  source $HOME/.local/bin/env
else
  echo "uv already installed, skipping."
fi

# -----------------------------
# Final checks
# -----------------------------
echo "=== Versions ==="
docker --version
uv --version

echo
echo "✅ Installation complete."
echo "⚠️  You may need to log out and back in for Docker group changes to take effect."
