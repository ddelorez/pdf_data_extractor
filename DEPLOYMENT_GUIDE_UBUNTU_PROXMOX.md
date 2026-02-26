# PDF Extractor - Ubuntu/Proxmox VE Deployment Guide

**Version**: 2.0.0  
**Last Updated**: February 2026  
**Status**: Production Ready

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Proxmox VE VM Creation](#proxmox-ve-vm-creation)
4. [Ubuntu Setup](#ubuntu-setup)
5. [Docker Installation](#docker-installation)
6. [Application Deployment](#application-deployment)
7. [Networking and Access](#networking-and-access)
8. [Configuration and Optimization](#configuration-and-optimization)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Recommended VM Sizing on Proxmox VE

#### Minimum Configuration (Development/Testing)
- **vCPU**: 2 cores
- **RAM**: 4 GB (2-4 GB guaranteed)
- **Storage**: 50 GB (SSD recommended)
- **Network**: 1 Gbps virtual NIC

#### Recommended Configuration (Production)
- **vCPU**: 4 cores
- **RAM**: 8 GB (4-8 GB guaranteed)
- **Storage**: 100 GB (SSD recommended, with separate volumes for uploads/outputs)
- **Network**: 1 Gbps virtual NIC (optional: redundant NICs for HA)

#### High-Capacity Configuration (Heavy Workloads)
- **vCPU**: 8+ cores
- **RAM**: 16+ GB
- **Storage**: 200+ GB SSD with dedicated LVM volumes for data
- **Network**: Dedicated 1 Gbps with quality of service (QoS) rules

### Storage Breakdown
- **OS/System**: 20 GB
- **Docker Images**: 15-20 GB
- **Application Data** (uploads/outputs): 40-60 GB (scalable)
- **Logs**: 5-10 GB (with rotation)

### Operating System
- **Ubuntu Version**: 22.04 LTS or 24.04 LTS (Recommended: 22.04 LTS for stability)
- **Kernel**: 5.15+ (automatically provided by Ubuntu)
- **Container Runtime**: Docker CE 20.10+ or Docker Engine 24.x

### Network Requirements
- **Connectivity**: At least 1 virtual NIC with access to Proxmox bridge network
- **Bandwidth**: Minimum 1 Gbps (for file upload throughput)
- **DNS**: Properly configured (local or external)
- **Firewall**: Ports 3000 (frontend), 5000 (backend - internal) accessible as needed

---

## Prerequisites

### On Proxmox VE Host
- Root or cluster administrator access to Proxmox VE
- Sufficient physical disk space for VM and snapshots
- At least 50 GB free space on storage backend
- Network connectivity configured in Proxmox cluster
- ISO image for Ubuntu Server 22.04 LTS uploaded to Proxmox

### On Ubuntu VM (Post-Installation)
- Ubuntu 22.04 LTS or 24.04 LTS installed with network connectivity
- User account with `sudo` privileges
- Terminal/SSH access to the Ubuntu VM
- At least 20 GB available disk space after OS installation

### Applications and Tools Required
The deployment process will install:
- Docker Engine (via official Docker repository)
- Docker Compose (v2.x via Docker installation)
- Git (for cloning repository if needed)
- curl/wget (for downloading files)
- Python runtime (included in Docker images)
- Node.js runtime (included in Docker images)

---

## Proxmox VE VM Creation

### Step 1: Prepare Ubuntu Server 22.04 LTS ISO

1. Log into your Proxmox VE cluster
2. Navigate to **Datacenter** → **Storage** → select your storage backend
3. Click **Upload** and select Ubuntu Server 22.04 LTS ISO file
4. Wait for upload to complete

### Step 2: Create VM in Proxmox VE

1. In Proxmox Web UI, click **Create VM**

2. **General Settings**:
   - Node: Select your Proxmox node
   - VM ID: Assign a unique ID (e.g., 100)
   - Name: `pdf-extractor-prod` (or similar)
   - Resource Pool: Select or leave default

3. **OS Settings**:
   - Type: Linux
   - Version: 5.x - 6.x kernel
   - ISO image: Ubuntu Server 22.04 LTS

4. **System Settings**:
   - Machine: Default (q35)
   - BIOS: Default
   - Disable BIOS EFI: Leave unchecked

5. **Disk Settings**:
   - Storage: Select your SSD storage (e.g., `local-lvm`)
   - Size: Allocate minimum 50 GB for production
   - Leave other defaults as recommended

6. **CPU Settings**:
   - Type: Host (for best performance)
   - Cores: Set to 4 (recommended for production)
   - Sockets: 1

7. **Memory Settings**:
   - Memory: Allocate 8 GB (8192 MB) for production
   - Minimum memory: 4 GB (4096 MB) - VM can balloon down

8. **Network Settings**:
   - Model: VirtIO (recommended for performance)
   - Bridge: Select your Proxmox bridge (usually `vmbr0`)
   - VLAN tag: Leave empty or specify network VLAN if needed

9. **Confirm and Create**:
   - Review settings and click **Finish**
   - Wait for VM creation to complete

### Step 3: Install Ubuntu Server

1. Start the VM (right-click → **Start**)
2. Open VM console or use VNC viewer
3. Follow Ubuntu Server 22.04 installation wizard:
   - Language: English
   - Keyboard: Select your layout
   - Network: Configure IPv4 (DHCP or static IP)
   - Storage: Accept default partitioning (full disk)
   - Account: Create user with strong password
   - SSH: Enable OpenSSH server (recommended)
   - Packages: Standard system utilities only
   - Finalize: Complete installation

4. Reboot when prompted

### Step 4: Post-Installation Configuration

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Set hostname (optional)
sudo hostnamectl set-hostname pdf-extractor

# Configure static IP (if preferred over DHCP)
sudo nano /etc/netplan/00-installer-config.yaml
# Edit: Set static IP, gateway, DNS

# Apply network changes
sudo netplan apply

# Enable SSH key-based authentication (recommended)
ssh-copy-id -i ~/.ssh/id_rsa.pub username@pdf-extractor-ip
```

---

## Docker Installation

### Step 1: Remove Old Docker Versions

```bash
# Remove conflicting packages if present
sudo apt-get remove -y docker docker-doc docker.io containerd runc 2>/dev/null || true
```

### Step 2: Install Docker Repository

```bash
# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Create Docker GPG key directory
sudo install -m 0755 -d /etc/apt/keyrings

# Download and setup Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set appropriate permissions
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### Step 3: Install Docker Engine and Compose

```bash
# Update package index
sudo apt-get update

# Install Docker Engine, CLI, Containerd, and Compose
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 4: Configure Docker for Non-Root User (Optional but Recommended)

```bash
# Create docker group (usually already exists)
sudo groupadd docker 2>/dev/null || true

# Add current user to docker group
sudo usermod -aG docker $USER

# Activate group membership (choose one method)
# Method 1: Log out and log back in
# Method 2: Use newgrp command
newgrp docker

# Verify by running docker without sudo
docker ps
```

### Step 5: Configure Docker Daemon for Production

```bash
# Create/edit Docker daemon configuration
sudo nano /etc/docker/daemon.json
```

Add the following configuration:

```json
{
  "debug": false,
  "live-restore": true,
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "10",
    "labels": "app=pdf-extractor"
  },
  "metrics-addr": "0.0.0.0:9323",
  "experimental": false,
  "insecure-registries": []
}
```

Then restart Docker:

```bash
# Reload Docker daemon configuration
sudo systemctl daemon-reload
sudo systemctl restart docker

# Verify Docker is running
sudo systemctl status docker
```

---

## Application Deployment

### Step 1: Prepare Application Directory

```bash
# Create application directory
sudo mkdir -p /opt/pdf-extractor
sudo chown $USER:$USER /opt/pdf-extractor

# Navigate to application directory
cd /opt/pdf-extractor

# Create data directories
mkdir -p {uploads,outputs,logs,templates}
chmod 755 {uploads,outputs,logs,templates}
```

### Step 2: Obtain Application Files

**Option A: Clone from Git Repository**

```bash
# Install git if not already installed
sudo apt-get install -y git

# Clone application repository
cd /opt/pdf-extractor
git clone https://your-repository-url.git .

# If you need to specify a branch
git clone -b main https://your-repository-url.git .
```

**Option B: Download Application Files**

```bash
# Download and extract application package
cd /opt/pdf-extractor
wget https://your-download-url/pdf-extractor-v2.0.0.tar.gz
tar -xzf pdf-extractor-v2.0.0.tar.gz
rm pdf-extractor-v2.0.0.tar.gz
```

### Step 3: Configure Environment

```bash
# Create .env file from template
cp .env.example .env

# Edit environment configuration
sudo nano .env
```

Update the following variables in `.env`:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-very-secure-secret-key-min-32-chars-change-this

# File Upload Configuration
MAX_UPLOAD_SIZE=104857600  # 100 MB in bytes
UPLOAD_FOLDER=/app/uploads
TEMPLATE_FOLDER=/app/templates
OUTPUT_FOLDER=/app/outputs

# Logging
LOG_LEVEL=INFO

# Server
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# CORS Configuration (adjust based on your frontend domain)
CORS_ORIGINS="http://localhost:3000,https://your-domain.com"

# PDF Processing
DEFAULT_TIMEOUT=30
MAX_BATCH_FILES=50
```

### Step 4: Generate Secure Secret Key

```bash
# Generate a secure SECRET_KEY (run from any Python-capable machine)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copy the output and update SECRET_KEY in .env file
```

### Step 5: Build and Run Docker Containers

#### Option A: Using Docker Compose

```bash
# Navigate to application directory
cd /opt/pdf-extractor

# Pull latest base images
docker compose pull

# Build application images
docker compose build

# Start containers in background (detached mode)
docker compose up -d

# View container logs
docker compose logs -f

# Check container status
docker compose ps
```

#### Option B: Manual Docker Commands (if not using docker-compose)

```bash
# Build backend image
docker build -t pdf-extractor:backend .

# Build frontend image
docker build -t pdf-extractor:frontend ./frontend

# Create custom network
docker network create pdf-extractor-network

# Run backend container
docker run -d \
  --name pdf-extractor-api \
  --network pdf-extractor-network \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-secure-key \
  -v /opt/pdf-extractor/uploads:/app/uploads \
  -v /opt/pdf-extractor/outputs:/app/outputs \
  -v /opt/pdf-extractor/logs:/app/logs \
  --log-driver json-file \
  --log-opt max-size=100m \
  --log-opt max-file=10 \
  pdf-extractor:backend

# Run frontend container
docker run -d \
  --name pdf-extractor-frontend \
  --network pdf-extractor-network \
  -p 3000:3000 \
  --log-driver json-file \
  --log-opt max-size=50m \
  --log-opt max-file=5 \
  pdf-extractor:frontend
```

### Step 6: Verify Deployment

```bash
# Check container status
docker compose ps

# Test backend health endpoint
curl http://localhost:5000/api/health

# Test frontend accessibility (from another machine)
curl -I http://localhost:3000

# View application logs
docker compose logs backend
docker compose logs frontend

# Monitor container resource usage
docker stats pdf-extractor-api pdf-extractor-frontend
```

---

## Networking and Access

### Step 1: Configure Firewall Rules

```bash
# Install and enable UFW firewall (if not already installed)
sudo apt-get install -y ufw

# Allow SSH (important: do this before enabling firewall)
sudo ufw allow 22/tcp

# Allow HTTP traffic
sudo ufw allow 80/tcp

# Allow HTTPS traffic
sudo ufw allow 443/tcp

# Allow Docker port (frontend)
sudo ufw allow 3000/tcp

# Enable firewall
sudo ufw enable

# Check firewall status and rules
sudo ufw status
```

### Step 2: Configure Port Forwarding on Proxmox Host (if needed)

If your VM is on a private network and needs external access:

```bash
# On Proxmox host, forward external ports to VM
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination [VM-IP]:3000
iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT --to-destination [VM-IP]:443
iptables -A FORWARD -p tcp -d [VM-IP] --dport 3000 -j ACCEPT
iptables -A FORWARD -p tcp -d [VM-IP] --dport 443 -j ACCEPT

# Save iptables rules (persistent)
sudo apt-get install iptables-persistent
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### Step 3: Configure Reverse Proxy with Nginx (Recommended)

```bash
# Install Nginx
sudo apt-get install -y nginx

# Create Nginx configuration for PDF Extractor
sudo tee /etc/nginx/sites-available/pdf-extractor > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 100M;
    }
}
EOF

# Enable the configuration
sudo ln -sf /etc/nginx/sites-available/pdf-extractor /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### Step 4: Configure SSL/TLS with Let's Encrypt (Recommended for Production)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain SSL certificate (replace with your domain)
sudo certbot certonly --nginx -d your-domain.com

# Update Nginx configuration with SSL
sudo tee /etc/nginx/sites-available/pdf-extractor > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    client_max_body_size 100M;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 100M;
    }
}
EOF

# Reload Nginx
sudo systemctl reload nginx

# Set up automatic certificate renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Step 5: Configure DNS Records

Add or update DNS records pointing to your server:

```
A Record:    your-domain.com      → [Your-Server-IP]
CNAME:       www.your-domain.com  → your-domain.com
```

---

## Configuration and Optimization

### Step 1: Enable Docker to Start on Boot

```bash
# Enable Docker service
sudo systemctl enable docker
sudo systemctl enable docker.socket

# Verify
sudo systemctl status docker
```

### Step 2: Create Systemd Service for Application

```bash
# Create systemd service file
sudo tee /etc/systemd/system/pdf-extractor.service > /dev/null <<EOF
[Unit]
Description=PDF Extractor Application (Docker Compose)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=/opt/pdf-extractor
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable pdf-extractor.service

# Verify
sudo systemctl status pdf-extractor.service
```

### Step 3: Configure Log Rotation

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/pdf-extractor > /dev/null <<EOF
/opt/pdf-extractor/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
    sharedscripts
    postrotate
        docker compose -f /opt/pdf-extractor/docker-compose.yml kill -s SIGUSR1 backend || true
    endscript
}
EOF

# Test logrotate configuration
sudo logrotate -d /etc/logrotate.d/pdf-extractor
```

### Step 4: Performance Tuning

#### Increase Limits for Large File Processing

```bash
# Edit system limits
sudo nano /etc/security/limits.conf

# Add the following lines:
# *               soft    nofile          524288
# *               hard    nofile          524288
# *               soft    nproc           524288
# *               hard    nproc           524288

# Apply changes (may require session restart)
sudo sysctl -p
```

#### Configure VM Swap and Memory

```bash
# Check current swap
swapon --show

# Allocate additional swap if needed (5GB example)
sudo fallocate -l 5G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent by adding to fstab
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Step 5: Backup Configuration

```bash
# Create backup script
sudo tee /opt/pdf-extractor/backup.sh > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups/pdf-extractor"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Stop containers (optional)
docker compose stop

# Backup application and data
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
  /opt/pdf-extractor \
  --exclude='uploads/*' \
  --exclude='outputs/*' \
  --exclude='.git'

# Backup persistent data
tar -czf $BACKUP_DIR/data_backup_$DATE.tar.gz \
  /opt/pdf-extractor/uploads \
  /opt/pdf-extractor/outputs \
  /opt/pdf-extractor/logs

# Start containers
docker compose start

# Keep only last 10 backups
find $BACKUP_DIR -name "*.tar.gz" -type f | sort -r | tail -n +11 | xargs rm -f

echo "Backup completed: $BACKUP_DIR/app_backup_$DATE.tar.gz"
echo "Data backup completed: $BACKUP_DIR/data_backup_$DATE.tar.gz"
EOF

# Make script executable
chmod +x /opt/pdf-extractor/backup.sh

# Schedule daily backup via cron
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/pdf-extractor/backup.sh") | crontab -
```

---

## Monitoring and Maintenance

### Step 1: Container Health Monitoring

```bash
# Check container health status
docker compose ps

# View real-time container metrics
docker stats --no-stream pdf-extractor-api pdf-extractor-frontend

# Enable detailed monitoring with docker events
docker events --filter 'container=pdf-extractor-api' --filter 'container=pdf-extractor-frontend'
```

### Step 2: Log Monitoring

```bash
# View combined logs from all containers
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# View frontend logs only
docker compose logs -f frontend

# View last 100 lines
docker compose logs --tail=100 backend

# Filter logs by timestamp
docker compose logs --since 2h backend
```

### Step 3: Disk Space Management

```bash
# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up unused Docker resources
docker system prune -a --volumes

# Clean up container logs
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

### Step 4: Regular Maintenance Tasks

**Weekly Tasks:**
```bash
# Check system updates
sudo apt list --upgradable

# Check container health
docker compose ps

# Review logs for errors
docker compose logs backend | grep ERROR
```

**Monthly Tasks:**
```bash
# Update Docker images
docker compose pull
docker compose up -d

# Update Ubuntu packages
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get autoremove -y

# Review disk usage and clean up
docker system prune -a

# Test backup restore procedure
# (Mandatory for production environments)
```

### Step 5: Resource Monitoring Dashboard (Optional)

```bash
# Portainer - Container management UI
docker volume create portainer_data

docker run -d \
  -p 8000:8000 \
  -p 9000:9000 \
  --name=portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

# Access Portainer at http://localhost:9000
```

---

## Troubleshooting

### Frontend Not Connecting to Backend

**Symptoms**: Frontend loads but shows connection errors

**Solutions**:
```bash
# 1. Check backend container is running
docker compose ps backend

# 2. Verify backend health
curl http://localhost:5000/api/health

# 3. Check CORS configuration in .env
grep CORS_ORIGINS .env

# 4. Review backend logs
docker compose logs backend

# 5. Check network connectivity between containers
docker network inspect pdf-extractor-network

# 6. Rebuild containers
docker compose down
docker compose build
docker compose up -d
```

### Container Exits Immediately

**Symptoms**: `docker compose ps` shows container status as "exited"

**Solutions**:
```bash
# 1. Check container startup error
docker compose logs backend -n 50

# 2. Verify environment variables
docker compose exec backend env

# 3. Check file permissions
ls -la /opt/pdf-extractor/{uploads,outputs,logs,templates}

# 4. Test image manually
docker run -it pdf-extractor:backend /bin/bash

# 5. Rebuild image from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Files Not Persisting on Upload

**Symptoms**: Uploaded files disappear after container restart

**Solutions**:
```bash
# 1. Verify volumes are mounted
docker compose exec backend mount | grep uploads

# 2. Check host directory permissions
ls -la /opt/pdf-extractor/uploads

# 3. Inspect volume mounts in compose file
grep -A 5 "volumes:" docker-compose.yml

# 4. Check Docker daemon log
sudo journalctl -u docker -n 50

# 5. Remount volume and restart
docker compose down
sudo chown $(id -u):$(id -g) /opt/pdf-extractor/uploads
docker compose up -d
```

### High Memory Usage

**Symptoms**: Container memory usage exceeds limits

**Solutions**:
```bash
# 1. Check memory limits
docker compose ps --no-trunc

# 2. Monitor memory in real-time
docker stats --no-stream pdf-extractor-api

# 3. Analyze backend process usage
docker compose exec backend ps aux

# 4. Review application logs for memory leaks
docker compose logs backend | grep -i memory

# 5. Increase memory allocation in docker-compose.yml
# Edit deploy.resources.limits.memory

# 6. Restart container
docker compose restart backend
```

### SSL Certificate Issues

**Symptoms**: HTTPS connection fails or certificate warnings

**Solutions**:
```bash
# 1. Check certificate expiration
sudo certbot certificates

# 2. Verify Nginx SSL configuration
sudo nginx -T

# 3. Test SSL connection
openssl s_client -connect your-domain.com:443

# 4. Force certificate renewal (if needed)
sudo certbot renew --force-renewal

# 5. Check certificate file permissions
sudo ls -la /etc/letsencrypt/live/your-domain.com/

# 6. Reload Nginx after certificate update
sudo systemctl reload nginx
```

### Docker Daemon Crashes or Restarts

**Symptoms**: Containers stop unexpectedly, Docker service restarts

**Solutions**:
```bash
# 1. Check Docker daemon status
sudo systemctl status docker

# 2. View Docker daemon logs
sudo journalctl -u docker -n 100

# 3. Check system resources
free -h
df -h

# 4. Verify Docker configuration
cat /etc/docker/daemon.json

# 5. Check for disk space issues and clean up
docker system prune -a --volumes

# 6. Restart Docker daemon
sudo systemctl restart docker

# 7. Check for kernel issues
sudo dmesg | tail -50
```

### API Endpoints Returning 502 Bad Gateway

**Symptoms**: Frontend shows "Bad Gateway" error, Nginx logs show 502

**Solutions**:
```bash
# 1. Check backend container status
docker compose ps backend

# 2. Verify backend is responding
curl -v http://localhost:5000/api/health

# 3. Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# 4. Verify backend socket/port
netstat -tuln | grep 5000

# 5. Check Nginx upstream configuration
sudo grep -A 5 "upstream" /etc/nginx/sites-enabled/pdf-extractor

# 6. Restart backend and Nginx
docker compose restart backend
sudo systemctl restart nginx
```

### Unable to Upload Files (413 Payload Too Large)

**Symptoms**: File upload fails with 413 error

**Solutions**:
```bash
# 1. Check MAX_UPLOAD_SIZE in .env
grep MAX_UPLOAD_SIZE .env

# 2. Verify Nginx client_max_body_size
grep client_max_body_size /etc/nginx/sites-enabled/pdf-extractor

# 3. Update Nginx configuration if needed
sudo nano /etc/nginx/sites-available/pdf-extractor
# Set: client_max_body_size 100M;

# 4. Test backend upload limit
docker compose exec backend curl -X POST \
  -F "file=@testfile.pdf" \
  http://localhost:5000/api/extract

# 5. Reload services
sudo systemctl reload nginx
docker compose restart backend
```

### General Debugging Steps

```bash
# 1. Collect system information
uname -a
docker --version
docker compose version

# 2. Check all containers and networks
docker ps -a
docker network ls

# 3. Validate docker-compose syntax
docker compose config

# 4. Collect all application logs
docker compose logs --all > /tmp/app_logs.txt

# 5. Check Proxmox VM resource allocation
# (From Proxmox host)
proxmox vm list
pvesh get /nodes/[node-name]/qemu/[vm-id]/status/current

# 6. Enable debug logging in .env
LOG_LEVEL=DEBUG

# 7. Restart everything in safe order
docker compose down
docker system prune -f
docker compose up -d
```

---

## Emergency Recovery

### Restore from Backup

```bash
# 1. Stop containers
docker compose stop

# 2. Restore application
cd /opt
sudo rm -rf pdf-extractor
sudo tar -xzf /backups/pdf-extractor/app_backup_20240226_020000.tar.gz

# 3. Restore data
tar -xzf /backups/pdf-extractor/data_backup_20240226_020000.tar.gz -C /opt/pdf-extractor

# 4. Verify permissions
sudo chown -R $USER:$USER /opt/pdf-extractor

# 5. Start containers
cd /opt/pdf-extractor
docker compose up -d

# 6. Verify restoration
docker compose ps
curl http://localhost:5000/api/health
```

### Reset Docker and Containers

```bash
# WARNING: This will delete all containers and volumes

# 1. Stop all containers
docker compose down -v

# 2. Remove unused Docker objects
docker system prune -a --volumes

# 3. Restart Docker daemon
sudo systemctl restart docker

# 4. Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

---

## Production Deployment Checklist

- [ ] Ubuntu 22.04 LTS installed on Proxmox VM
- [ ] VM allocated with recommended resources (4vCPU, 8GB RAM, 100GB SSD)
- [ ] Docker and Docker Compose installed and tested
- [ ] Application files obtained and extracted to `/opt/pdf-extractor`
- [ ] Environment variables configured in `.env` file
- [ ] SECRET_KEY generated and updated in `.env`
- [ ] Docker images built successfully
- [ ] Containers running and accessible
- [ ] Health endpoints responding (backend: `:5000/api/health`)
- [ ] Frontend UI loads and connects to backend
- [ ] Firewall rules configured for HTTP/HTTPS
- [ ] Nginx reverse proxy configured and tested
- [ ] SSL certificate installed (Let's Encrypt or other)
- [ ] Systemd service created for auto-start
- [ ] Log rotation configured
- [ ] Backup schedule established
- [ ] Monitoring and alerting configured
- [ ] Documented network topology and access points
- [ ] Team trained on basic operations and troubleshooting
- [ ] Runbook and emergency procedures documented

---

## Support and Documentation

For additional information:
- **Application Documentation**: See README.md in project root
- **Docker Logs**: `docker compose logs -f [service]`
- **System Logs**: `sudo journalctl -u docker -n 100`
- **Nginx Logs**: `/var/log/nginx/{access,error}.log`

For issues or bugs:
1. Check the Troubleshooting section above
2. Review application logs: `docker compose logs backend`
3. Check system resources: `docker stats`, `free -h`, `df -h`
4. Validate configuration: `docker compose config`

---

**Document Version**: 2.0.0  
**Last Updated**: February 2026  
**Status**: Production Ready
