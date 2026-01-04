# Synology DS923+ Deployment Guide

Complete guide for deploying EmpathicGateway on Synology DS923+ NAS with external access.

---

## 📋 Prerequisites

- Synology DS923+ NAS
- DSM 7.0 or higher
- 8GB+ RAM recommended (4GB minimum)
- Internet connection
- Router admin access (for port forwarding)

---

## 🚀 Quick Start (5 Minutes)

### Option 1: Using Container Manager (Easiest)

1. **Install Container Manager**
   - Open Package Center
   - Search "Container Manager"
   - Click Install

2. **Create Project**
   ```
   Container Manager → Project → Create
   - Project Name: empathicgateway
   - Path: /docker/empathicgateway
   - Source: Upload docker-compose.yml
   ```

3. **Upload Files**
   - Download project from GitHub
   - Upload `docker-compose.yml`
   - Click "Build"

4. **Access**
   - Frontend: `http://nas-ip:8503`
   - Backend: `http://nas-ip:8081`

---

## 🐳 Option 2: SSH + Docker Compose (Recommended)

### Step 1: Enable SSH

```
Control Panel → Terminal & SNMP
☑ Enable SSH service
Port: 22
```

### Step 2: Connect to NAS

```bash
ssh admin@your-nas-ip
# Enter your DSM password
```

### Step 3: Install Git (if not installed)

```bash
# Install Git via Package Center or:
sudo synopkg install Git
```

### Step 4: Clone Repository

```bash
cd /volume1/docker
git clone https://github.com/mmapce/empathicgateway.git
cd empathicgateway
```

### Step 5: Deploy with Docker Compose

```bash
# Start services
sudo docker-compose up -d

# Check status
sudo docker-compose ps

# View logs
sudo docker-compose logs -f
```

### Step 6: Verify Deployment

```bash
# Test backend
curl http://localhost:8081/health

# Expected response:
# {"status":"healthy","model_loaded":true,"ner_loaded":true}
```

---

## 🌐 External Access Setup

### Method 1: Synology QuickConnect (Easiest)

**Pros:** No router config, automatic SSL  
**Cons:** Slower than direct access

1. **Enable QuickConnect**
   ```
   Control Panel → QuickConnect
   ☑ Enable QuickConnect
   QuickConnect ID: your-unique-name
   ```

2. **Access URL**
   ```
   https://quickconnect.to/your-unique-name:8503
   ```

3. **Configure Reverse Proxy** (Optional)
   ```
   Control Panel → Login Portal → Advanced → Reverse Proxy
   
   Create Rule:
   - Description: EmpathicGateway Frontend
   - Source: your-unique-name.synology.me
   - Port: 443
   - Destination: localhost
   - Port: 8503
   ```

---

### Method 2: DDNS + Port Forwarding (Fast)

**Pros:** Fast, direct access  
**Cons:** Requires router configuration

#### Step 1: Enable DDNS

```
Control Panel → External Access → DDNS
☑ Enable DDNS
Service Provider: Synology
Hostname: your-name.synology.me
```

#### Step 2: Configure Router Port Forwarding

**Example (TP-Link Router):**
```
Router Admin Panel → Forwarding → Virtual Servers

Add Rules:
1. Frontend
   - Service Port: 8503
   - Internal Port: 8503
   - IP Address: [NAS IP]
   - Protocol: TCP

2. Backend  
   - Service Port: 8081
   - Internal Port: 8081
   - IP Address: [NAS IP]
   - Protocol: TCP

3. HTTPS (Optional)
   - Service Port: 443
   - Internal Port: 443
   - IP Address: [NAS IP]
   - Protocol: TCP
```

#### Step 3: Enable SSL Certificate

```
Control Panel → Security → Certificate
Add → Get a certificate from Let's Encrypt

Domain name: your-name.synology.me
Email: your-email@example.com
☑ Set as default certificate
```

#### Step 4: Configure Reverse Proxy with SSL

```
Control Panel → Login Portal → Advanced → Reverse Proxy

Rule 1: Frontend HTTPS
- Source:
  Protocol: HTTPS
  Hostname: your-name.synology.me
  Port: 443
- Destination:
  Protocol: HTTP
  Hostname: localhost
  Port: 8503
☑ Enable HSTS

Rule 2: Backend API
- Source:
  Protocol: HTTPS
  Hostname: api.your-name.synology.me
  Port: 443
- Destination:
  Protocol: HTTP
  Hostname: localhost
  Port: 8081
```

#### Step 5: Update Frontend API URL

```bash
# SSH to NAS
ssh admin@your-nas-ip

# Edit docker-compose.yml
cd /volume1/docker/empathicgateway
sudo nano docker-compose.yml

# Update frontend environment:
environment:
  - API_URL=https://api.your-name.synology.me

# Restart
sudo docker-compose down
sudo docker-compose up -d
```

**Access URLs:**
- Frontend: `https://your-name.synology.me`
- Backend: `https://api.your-name.synology.me`

---

### Method 3: Tailscale VPN (Most Secure)

**Pros:** Encrypted, no port forwarding, zero-config  
**Cons:** Requires VPN client on devices

#### Step 1: Install Tailscale on NAS

```bash
# SSH to NAS
ssh admin@your-nas-ip

# Download Tailscale
wget https://pkgs.tailscale.com/stable/tailscale_1.56.1_amd64.tgz
tar xzf tailscale_1.56.1_amd64.tgz
cd tailscale_1.56.1_amd64

# Start Tailscale
sudo ./tailscaled &
sudo ./tailscale up

# Follow the authentication link
# Your NAS will get a Tailscale IP (e.g., 100.x.x.x)
```

#### Step 2: Install Tailscale on Your Devices

- **Mac/Windows:** https://tailscale.com/download
- **iOS/Android:** App Store / Play Store
- **Linux:** `curl -fsSL https://tailscale.com/install.sh | sh`

#### Step 3: Access via Tailscale

```
Frontend: http://100.x.x.x:8503
Backend: http://100.x.x.x:8081
```

**Advantages:**
- ✅ Encrypted end-to-end
- ✅ Works from anywhere
- ✅ No exposed ports
- ✅ Free for personal use

---

### Method 4: Cloudflare Tunnel (Professional)

**Pros:** DDoS protection, global CDN, free  
**Cons:** Requires Cloudflare account

#### Step 1: Install Cloudflared

```bash
# SSH to NAS
ssh admin@your-nas-ip

# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

#### Step 2: Authenticate

```bash
cloudflared tunnel login
# Follow the browser link to authenticate
```

#### Step 3: Create Tunnel

```bash
# Create tunnel
cloudflared tunnel create empathic-gateway

# Note the Tunnel ID (e.g., abc123...)

# Create config
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

**Config file:**
```yaml
tunnel: abc123-your-tunnel-id
credentials-file: /root/.cloudflared/abc123-your-tunnel-id.json

ingress:
  - hostname: empathic.your-domain.com
    service: http://localhost:8503
  - hostname: api.empathic.your-domain.com
    service: http://localhost:8081
  - service: http_status:404
```

#### Step 4: Configure DNS

```bash
# Add DNS records
cloudflared tunnel route dns empathic-gateway empathic.your-domain.com
cloudflared tunnel route dns empathic-gateway api.empathic.your-domain.com
```

#### Step 5: Run Tunnel

```bash
# Start tunnel
cloudflared tunnel run empathic-gateway

# Or as a service (auto-start)
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

**Access URLs:**
- Frontend: `https://empathic.your-domain.com`
- Backend: `https://api.empathic.your-domain.com`

---

## 🔒 Security Best Practices

### 1. Enable Firewall

```
Control Panel → Security → Firewall
☑ Enable firewall

Rules:
- Allow: 22 (SSH) - Your IP only
- Allow: 443 (HTTPS)
- Allow: 8503 (Frontend) - Optional
- Allow: 8081 (Backend) - Optional
- Deny: All others
```

### 2. Enable 2FA

```
Control Panel → User & Group → Advanced
☑ Enforce 2-step verification for all users
```

### 3. Auto-Block

```
Control Panel → Security → Protection
☑ Enable auto block
Login attempts: 5
Within: 5 minutes
Block for: 30 minutes
```

### 4. Regular Updates

```
Control Panel → Update & Restore
☑ Enable auto-update
```

### 5. Backup Configuration

```bash
# Backup docker-compose.yml
sudo cp docker-compose.yml docker-compose.yml.backup

# Backup entire project
sudo tar -czf empathicgateway-backup.tar.gz /volume1/docker/empathicgateway
```

---

## 📊 Performance Optimization

### 1. Increase RAM (Recommended)

```
DS923+ supports up to 32GB RAM
Recommended: 16GB for smooth BERT inference
```

### 2. Enable SSD Cache

```
Storage Manager → SSD Cache → Create
- Read-Write cache
- Size: 256GB+ recommended
- Assign to Volume 1
```

### 3. Docker Resource Limits

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          memory: 2G
```

### 4. Enable Hardware Transcoding (if available)

```
Container Manager → Settings
☑ Enable GPU acceleration
```

---

## 🔧 Troubleshooting

### Backend Not Starting

```bash
# Check logs
sudo docker-compose logs backend

# Common issues:
# 1. Port conflict
sudo netstat -tulpn | grep 8081

# 2. Memory issue
free -h

# 3. Model loading failure
sudo docker-compose exec backend cat /app/backend/urgency_model.joblib
```

### Frontend Can't Connect to Backend

```bash
# Check network
sudo docker network ls
sudo docker network inspect empathicgateway_default

# Test connectivity
sudo docker-compose exec frontend curl http://backend:8081/health
```

### SSL Certificate Issues

```bash
# Renew Let's Encrypt
Control Panel → Security → Certificate → Renew

# Check certificate validity
openssl s_client -connect your-name.synology.me:443
```

### Port Forwarding Not Working

```bash
# Test from external network (use phone 4G)
curl https://your-name.synology.me:8503

# Check router NAT loopback
# Some routers don't support accessing public IP from LAN
```

---

## 📱 Mobile Access

### iOS Shortcut

```
1. Open Shortcuts app
2. Create new shortcut
3. Add "Open URL"
4. URL: https://your-name.synology.me
5. Add to Home Screen
```

### Android Widget

```
1. Long press home screen
2. Add widget → Chrome
3. Select bookmark: EmpathicGateway
```

---

## 🔄 Auto-Update Setup

### Create Update Script

```bash
sudo nano /volume1/docker/empathicgateway/update.sh
```

**Script content:**
```bash
#!/bin/bash

cd /volume1/docker/empathicgateway

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f

echo "Update completed at $(date)"
```

### Make Executable

```bash
sudo chmod +x /volume1/docker/empathicgateway/update.sh
```

### Schedule with Task Scheduler

```
Control Panel → Task Scheduler → Create → Scheduled Task → User-defined script

General:
- Task: Update EmpathicGateway
- User: root

Schedule:
- Run on: Weekly
- Day: Sunday
- Time: 03:00

Task Settings:
- User-defined script:
  /volume1/docker/empathicgateway/update.sh
```

---

## 📊 Monitoring

### Resource Usage

```bash
# CPU and Memory
sudo docker stats

# Disk usage
sudo docker system df
```

### Application Logs

```bash
# Real-time logs
sudo docker-compose logs -f

# Last 100 lines
sudo docker-compose logs --tail=100

# Specific service
sudo docker-compose logs backend
```

### Health Checks

```bash
# Backend health
curl http://localhost:8081/health

# Frontend health
curl http://localhost:8503
```

---

## 🎯 Recommended Setup

**For Home Use:**
```
1. QuickConnect (easy access)
2. Tailscale VPN (secure management)
3. Let's Encrypt SSL
4. Auto-updates enabled
```

**For Production:**
```
1. DDNS + Port Forwarding
2. Cloudflare Tunnel (DDoS protection)
3. Reverse Proxy with SSL
4. Firewall + 2FA
5. SSD Cache
6. 16GB RAM
```

---

## 📚 Additional Resources

- [Synology Docker Guide](https://www.synology.com/en-global/dsm/packages/Docker)
- [Let's Encrypt Setup](https://www.synology.com/en-global/knowledgebase/DSM/tutorial/Network/How_to_enable_HTTPS_and_create_a_certificate_signing_request_on_your_Synology_NAS)
- [Tailscale Documentation](https://tailscale.com/kb/1131/synology/)
- [Cloudflare Tunnel Guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

---

## 🆘 Support

**Issues?**
- Check logs: `sudo docker-compose logs`
- Restart services: `sudo docker-compose restart`
- Full reset: `sudo docker-compose down && sudo docker-compose up -d`

**Need Help?**
- GitHub Issues: https://github.com/mmapce/empathicgateway/issues
- Synology Community: https://community.synology.com/

---

## ✅ Deployment Checklist

- [ ] Container Manager installed
- [ ] Project deployed
- [ ] Backend health check passes
- [ ] Frontend accessible
- [ ] External access configured (choose method)
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] 2FA enabled
- [ ] Auto-updates scheduled
- [ ] Backup configured
- [ ] Mobile access tested

---

**Congratulations! Your EmpathicGateway is now running on Synology DS923+!** 🎉
