#!/bin/bash
set -e

# App-Sink Setup Script
# Installs K3s, App-Sink API, and CLI on a fresh VM

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
   ___                 _____ _       _
  / _ \               /  ___(_)     | |
 / /_\ \_ __  _ __    \ `--. _ _ __ | | __
 |  _  | '_ \| '_ \    `--. \ | '_ \| |/ /
 | | | | |_) | |_) |  /\__/ / | | | |   <
 \_| |_/ .__/| .__/   \____/|_|_| |_|_|\_\
       | |   | |
       |_|   |_|
EOF
echo -e "${NC}"

echo -e "${GREEN}App-Sink Kubernetes Abstraction Layer Setup${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (use sudo)${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Cannot detect OS${NC}"
    exit 1
fi

echo -e "${YELLOW}Detected OS: $OS${NC}"

# Check system requirements
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
CPU_CORES=$(nproc)

echo "System Resources:"
echo "  RAM: ${TOTAL_RAM}MB"
echo "  CPU Cores: ${CPU_CORES}"
echo ""

if [ $TOTAL_RAM -lt 3072 ]; then
    echo -e "${YELLOW}Warning: Less than 4GB RAM detected. App-Sink will work but performance may be limited.${NC}"
fi

if [ $CPU_CORES -lt 2 ]; then
    echo -e "${YELLOW}Warning: Less than 2 CPU cores detected. Performance may be limited.${NC}"
fi

# Ask for configuration
echo -e "${BLUE}Configuration:${NC}"
read -p "Enter domain for App-Sink API (e.g., api.example.com): " API_DOMAIN
read -p "Enter email for Let's Encrypt SSL certificates: " LETSENCRYPT_EMAIL

# Optional: AI Configuration
echo ""
echo "AI Configuration (for CLI auto-deployment):"
read -p "AI Provider (anthropic/openai) [anthropic]: " AI_PROVIDER
AI_PROVIDER=${AI_PROVIDER:-anthropic}
read -sp "AI API Key (leave empty to configure later): " AI_API_KEY
echo ""

echo ""
echo -e "${GREEN}Starting installation...${NC}"
echo ""

# 1. Install K3s
echo -e "${BLUE}[1/7] Installing K3s...${NC}"

if command -v k3s &> /dev/null; then
    echo "K3s already installed, skipping..."
else
    curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--write-kubeconfig-mode 644 --disable traefik" sh -

    # Wait for K3s to be ready
    echo "Waiting for K3s to be ready..."
    sleep 10
    k3s kubectl wait --for=condition=Ready node --all --timeout=120s
fi

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

echo -e "${GREEN}✓ K3s installed${NC}"

# 2. Install Traefik with Let's Encrypt
echo -e "${BLUE}[2/7] Installing Traefik Ingress Controller...${NC}"

# Add Traefik Helm repo
k3s kubectl create namespace traefik || true

# Create Let's Encrypt staging issuer first for testing
cat <<EOF | k3s kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: traefik
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: traefik-config
  namespace: traefik
data:
  traefik.yaml: |
    entryPoints:
      web:
        address: ":80"
        http:
          redirections:
            entryPoint:
              to: websecure
              scheme: https
      websecure:
        address: ":443"
        http:
          tls:
            certResolver: letsencrypt

    certificatesResolvers:
      letsencrypt:
        acme:
          email: ${LETSENCRYPT_EMAIL}
          storage: /data/acme.json
          httpChallenge:
            entryPoint: web

    providers:
      kubernetesCRD: {}
      kubernetesIngress: {}

    api:
      dashboard: true
      insecure: false
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: traefik
  namespace: traefik
spec:
  replicas: 1
  selector:
    matchLabels:
      app: traefik
  template:
    metadata:
      labels:
        app: traefik
    spec:
      serviceAccountName: traefik
      containers:
      - name: traefik
        image: traefik:v2.10
        ports:
        - name: web
          containerPort: 80
        - name: websecure
          containerPort: 443
        - name: admin
          containerPort: 8080
        volumeMounts:
        - name: config
          mountPath: /etc/traefik
        - name: data
          mountPath: /data
      volumes:
      - name: config
        configMap:
          name: traefik-config
      - name: data
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: traefik
  namespace: traefik
spec:
  type: LoadBalancer
  selector:
    app: traefik
  ports:
  - name: web
    port: 80
    targetPort: 80
  - name: websecure
    port: 443
    targetPort: 443
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: traefik
  namespace: traefik
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: traefik
rules:
- apiGroups: [""]
  resources: ["services", "endpoints", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions", "networking.k8s.io"]
  resources: ["ingresses", "ingressclasses"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions", "networking.k8s.io"]
  resources: ["ingresses/status"]
  verbs: ["update"]
- apiGroups: ["traefik.containo.us"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: traefik
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: traefik
subjects:
- kind: ServiceAccount
  name: traefik
  namespace: traefik
EOF

k3s kubectl wait --for=condition=available --timeout=120s deployment/traefik -n traefik

echo -e "${GREEN}✓ Traefik installed${NC}"

# 3. Install PostgreSQL for App-Sink metadata
echo -e "${BLUE}[3/7] Installing PostgreSQL...${NC}"

if command -v psql &> /dev/null; then
    echo "PostgreSQL already installed, skipping..."
else
    if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        apt-get update
        apt-get install -y postgresql postgresql-contrib
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
        dnf install -y postgresql-server postgresql-contrib
        postgresql-setup --initdb
    fi

    systemctl enable postgresql
    systemctl start postgresql
fi

# Create database and user
DB_PASSWORD=$(openssl rand -base64 32)
sudo -u postgres psql -c "CREATE DATABASE app_sink;" || true
sudo -u postgres psql -c "CREATE USER app_sink WITH ENCRYPTED PASSWORD '${DB_PASSWORD}';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE app_sink TO app_sink;" || true

echo -e "${GREEN}✓ PostgreSQL installed${NC}"

# 4. Install Python and dependencies
echo -e "${BLUE}[4/7] Installing Python dependencies...${NC}"

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get install -y python3 python3-pip python3-venv
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    dnf install -y python3 python3-pip
fi

echo -e "${GREEN}✓ Python installed${NC}"

# 5. Install App-Sink API
echo -e "${BLUE}[5/7] Installing App-Sink API...${NC}"

mkdir -p /opt/app-sink
cp -r api /opt/app-sink/
cd /opt/app-sink/api

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create configuration
mkdir -p /etc/app-sink
cat > /etc/app-sink/config.yaml <<EOF
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  url: postgresql://app_sink:${DB_PASSWORD}@localhost/app_sink

kubernetes:
  kubeconfig: /etc/rancher/k3s/k3s.yaml
  namespace_prefix: app-

ingress:
  class: traefik
  tls_issuer: letsencrypt
  default_domain: ${API_DOMAIN}

ai:
  provider: ${AI_PROVIDER}
  api_key: ${AI_API_KEY}
  model: ${AI_PROVIDER == 'anthropic' ? 'claude-3-5-sonnet-20241022' : 'gpt-4'}

api:
  domain: ${API_DOMAIN}
  admin_email: ${LETSENCRYPT_EMAIL}
EOF

# Run database migrations
python -m alembic upgrade head

# Create systemd service
cat > /etc/systemd/system/app-sink-api.service <<EOF
[Unit]
Description=App-Sink API Service
After=network.target postgresql.service k3s.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/app-sink/api
Environment="PATH=/opt/app-sink/api/venv/bin"
ExecStart=/opt/app-sink/api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable app-sink-api
systemctl start app-sink-api

echo -e "${GREEN}✓ App-Sink API installed${NC}"

# 6. Install CLI
echo -e "${BLUE}[6/7] Installing App-Sink CLI...${NC}"

cd /opt/app-sink
cp -r cli /opt/app-sink/
cd cli
/opt/app-sink/api/venv/bin/pip install -e .

# Make CLI available globally
ln -sf /opt/app-sink/api/venv/bin/app-sink /usr/local/bin/app-sink

echo -e "${GREEN}✓ CLI installed${NC}"

# 7. Create initial API key
echo -e "${BLUE}[7/7] Creating initial API key...${NC}"

INITIAL_API_KEY=$(/opt/app-sink/api/venv/bin/python -c "
import sys
sys.path.append('/opt/app-sink/api')
from core.auth import generate_api_key
print(generate_api_key('default'))
")

echo "$INITIAL_API_KEY" > /etc/app-sink/initial-api-key.txt
chmod 600 /etc/app-sink/initial-api-key.txt

echo -e "${GREEN}✓ API key created${NC}"

# Setup complete
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  App-Sink Installation Complete! 🚀${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Access Information:"
echo "  API Endpoint: https://${API_DOMAIN}"
echo "  API Key: ${INITIAL_API_KEY}"
echo "  Kubernetes Config: /etc/rancher/k3s/k3s.yaml"
echo ""
echo "Next Steps:"
echo ""
echo "1. Configure DNS:"
echo "   Point ${API_DOMAIN} to this server's IP address"
echo ""
echo "2. Configure CLI:"
echo "   app-sink config set endpoint https://${API_DOMAIN}"
echo "   app-sink config set api-key ${INITIAL_API_KEY}"
echo ""
echo "3. Deploy your first app:"
echo "   cd your-app-directory"
echo "   app-sink deploy"
echo ""
echo "4. Check status:"
echo "   app-sink list"
echo "   systemctl status app-sink-api"
echo "   systemctl status k3s"
echo ""
echo "Documentation: https://github.com/yourusername/app-sink"
echo ""
echo -e "${YELLOW}Important: Save the API key above - it won't be shown again!${NC}"
echo -e "${YELLOW}Stored in: /etc/app-sink/initial-api-key.txt${NC}"
