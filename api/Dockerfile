FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

ARG DEBIAN_MIRROR=https://mirrors.aliyun.com/debian
ARG DEBIAN_SECURITY_MIRROR=https://mirrors.aliyun.com/debian-security

# python:3.14-slim uses Debian's deb822 sources file. Keep the fallback for
# older slim variants that still provide /etc/apt/sources.list.
RUN set -eux; \
    for source_file in /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list; do \
        if [ -f "$source_file" ]; then \
            sed -i \
                -e "s|https\?://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
                -e "s|https\?://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
                -e "s|https\?://deb.debian.org/debian|${DEBIAN_MIRROR}|g" \
                "$source_file"; \
        fi; \
    done; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        git curl ca-certificates \
    ; \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ARG TRUFFLEHOG_VERSION=3.97.1
ARG GITLEAKS_VERSION=8.24.2
RUN curl -fsSL -o /tmp/trufflehog.tar.gz \
        "https://github.com/trufflesecurity/trufflehog/releases/download/v${TRUFFLEHOG_VERSION}/trufflehog_${TRUFFLEHOG_VERSION}_linux_amd64.tar.gz" \
    && tar -xzf /tmp/trufflehog.tar.gz -C /usr/local/bin trufflehog \
    && rm /tmp/trufflehog.tar.gz \
    && chmod +x /usr/local/bin/trufflehog \
    && trufflehog --version

RUN curl -fsSL -o /tmp/gitleaks.tar.gz \
        "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
    && tar -xzf /tmp/gitleaks.tar.gz -C /usr/local/bin gitleaks \
    && rm /tmp/gitleaks.tar.gz \
    && chmod +x /usr/local/bin/gitleaks \
    && gitleaks version

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "api.wsgi:application"]
