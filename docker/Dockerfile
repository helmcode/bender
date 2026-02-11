FROM python:3.12-slim

ARG KUBECTL_VERSION=1.32.1
ARG VAULT_VERSION=1.18.4
ARG ARGOCD_VERSION=2.13.3
ARG TARGETARCH

# System dependencies + Node.js + Claude Code CLI
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip ca-certificates jq openssh-client && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g @anthropic-ai/claude-code && \
    # kubectl
    curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
      -o /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl && \
    # vault
    curl -fsSL "https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_${TARGETARCH}.zip" \
      -o /tmp/vault.zip && unzip /tmp/vault.zip -d /usr/local/bin && rm /tmp/vault.zip && \
    # argocd
    curl -fsSL "https://github.com/argoproj/argo-cd/releases/download/v${ARGOCD_VERSION}/argocd-linux-${TARGETARCH}" \
      -o /usr/local/bin/argocd && chmod +x /usr/local/bin/argocd && \
    # aws cli
    AWS_ARCH=$([ "${TARGETARCH}" = "arm64" ] && echo "aarch64" || echo "x86_64") && \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" \
      -o /tmp/awscliv2.zip && unzip /tmp/awscliv2.zip -d /tmp && \
      /tmp/aws/install && rm -rf /tmp/awscliv2.zip /tmp/aws && \
    # cleanup
    apt-get purge -y unzip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["python", "-m", "bender"]
