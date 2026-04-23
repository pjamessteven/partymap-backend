# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git qtbase5-dev qtchooser qt5-qmake qtbase5-dev-tools \
    pyqt5-dev postgresql ffmpeg python3-dev \
    libatlas-base-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Enable uv bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1

# Set up uv to use a virtual environment outside of /app (to avoid volume mount issues)
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Copy dependency files first (for better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-install-project

# Copy project files
COPY . .

# Sync again with project
RUN uv sync --frozen

# Expose port to host
EXPOSE 5000

# Run entrypoint.sh to init db
ENTRYPOINT ["/app/entrypoint.sh"]
