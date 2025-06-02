# Security Setup Guide for Jira Webhook Server

## Overview

This guide explains how to secure your Jira webhook server to meet production security requirements. Jira Cloud and most enterprise Jira instances require HTTPS webhooks for security.

## 🔒 Security Features

The secure webhook server includes:

- **HTTPS/SSL encryption** for all communications
- **Webhook authentication** with secret tokens
- **Request logging** without sensitive data exposure
- **IP filtering** capabilities
- **Self-signed certificate** fallback for development

## 🚀 Quick Start (Development)

For development/testing with self-signed certificates:

1. **Update your `.env` file:**
   ```env
   USE_SSL=true
   # Leave SSL_CERT_PATH and SSL_KEY_PATH empty for self-signed
   WEBHOOK_SECRET=dev_secret_123
   ```

2. **Run the secure server:**
   ```bash
   python secure_webhook_server.py
   ```

3. **Test the secure endpoint:**
   ```bash
   curl -k -X GET https://localhost:5000/health
   ```

**Note:** The `-k` flag ignores self-signed certificate warnings.

## 🏢 Production Setup

### Option 1: Let's Encrypt (Recommended)

Let's Encrypt provides free SSL certificates:

1. **Install Certbot:**
   ```bash
   # Ubuntu/Debian
   sudo apt install certbot
   
   # CentOS/RHEL
   sudo yum install certbot
   ```

2. **Get SSL certificate:**
   ```bash
   sudo certbot certonly --standalone -d your-domain.com
   ```

3. **Update `.env` file:**
   ```env
   USE_SSL=true
   SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
   SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
   WEBHOOK_SECRET=your_strong_secret_here
   ```

4. **Set up certificate renewal:**
   ```bash
   # Add to crontab for automatic renewal
   0 0,12 * * * certbot renew --quiet --post-hook "systemctl restart webhook-server"
   ```

### Option 2: Custom SSL Certificate

If you have your own SSL certificate:

1. **Copy certificate files to your server:**
   ```bash
   # Certificate file (includes full chain)
   /etc/ssl/certs/your-domain.crt
   
   # Private key file
   /etc/ssl/private/your-domain.key
   ```

2. **Update `.env` file:**
   ```env
   USE_SSL=true
   SSL_CERT_PATH=/etc/ssl/certs/your-domain.crt
   SSL_KEY_PATH=/etc/ssl/private/your-domain.key
   WEBHOOK_SECRET=your_strong_secret_here
   ```

3. **Set proper file permissions:**
   ```bash
   sudo chmod 644 /etc/ssl/certs/your-domain.crt
   sudo chmod 600 /etc/ssl/private/your-domain.key
   sudo chown root:ssl-cert /etc/ssl/private/your-domain.key
   ```

### Option 3: Reverse Proxy (Nginx/Apache)

Use a reverse proxy to handle SSL termination:

1. **Install Nginx:**
   ```bash
   sudo apt install nginx
   ```

2. **Create Nginx configuration:**
   ```nginx
   # /etc/nginx/sites-available/webhook-server
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
   
       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
   
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Run webhook server in HTTP mode:**
   ```env
   USE_SSL=false  # Nginx handles SSL
   WEBHOOK_PORT=5000
   ```

4. **Enable and start Nginx:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/webhook-server /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## 🔐 Webhook Authentication

### Setting Up Webhook Secret

1. **Generate a strong secret:**
   ```bash
   # Generate a random 32-character secret
   openssl rand -hex 32
   ```

2. **Add to `.env`:**
   ```env
   WEBHOOK_SECRET=your_generated_secret_here
   ```

3. **Configure Jira webhook:**
   - In Jira webhook settings, add custom header:
   - **Header Name:** `Authorization`
   - **Header Value:** `Bearer your_generated_secret_here`

### Testing Authentication

```bash
# Test without authentication (should fail)
curl -k -X POST https://localhost:5000/jira-webhook

# Test with correct authentication
curl -k -X POST https://localhost:5000/jira-webhook \
  -H "Authorization: Bearer your_generated_secret_here" \
  -H "Content-Type: application/json" \
  -d '{"webhookEvent":"test"}'
```

## 🛡️ Additional Security Measures

### Firewall Configuration

Restrict access to webhook port:

```bash
# UFW (Ubuntu)
sudo ufw allow from YOUR_JIRA_IP to any port 5000
sudo ufw deny 5000

# iptables
sudo iptables -A INPUT -p tcp -s YOUR_JIRA_IP --dport 5000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j DROP
```

### Rate Limiting

Add rate limiting to prevent abuse:

```python
# Install flask-limiter
pip install flask-limiter

# Add to secure_webhook_server.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/jira-webhook', methods=['POST'])
@limiter.limit("10 per minute")
@authenticate_webhook
def jira_webhook():
    # ... existing code
```

### Request Logging

Configure secure logging:

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('webhook.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

## 🔍 Verification Steps

### 1. SSL Certificate Verification

```bash
# Check certificate details
openssl x509 -in /path/to/certificate.pem -text -noout

# Test SSL connection
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### 2. Webhook Endpoint Testing

```bash
# Health check
curl -k https://your-domain.com:5000/health

# Expected response:
{
  "status": "healthy",
  "secure": true,
  "version": "2.0",
  ...
}
```

### 3. Jira Integration Test

```bash
# Manual ticket processing test
curl -k -X POST https://your-domain.com:5000/test-ticket/PROJ-123 \
  -H "Authorization: Bearer your_secret"
```

## 🚨 Security Checklist

Before going to production:

- [ ] SSL certificate is valid and not self-signed
- [ ] Webhook secret is configured and strong
- [ ] Firewall rules restrict access appropriately
- [ ] Rate limiting is enabled
- [ ] Logging is configured securely
- [ ] File permissions are correct (certificates)
- [ ] Regular security updates are scheduled
- [ ] Backup and disaster recovery plans are in place
- [ ] Monitoring and alerting are set up

## 🐛 Troubleshooting

### Common Issues

1. **"SSL certificate verify failed"**
   - Check certificate path and permissions
   - Verify certificate chain is complete
   - Test with `openssl s_client`

2. **"Connection refused"**
   - Check if server is running
   - Verify port is open in firewall
   - Check server logs

3. **"Unauthorized" responses**
   - Verify webhook secret matches
   - Check Authorization header format
   - Review authentication logs

### Debug Commands

```bash
# Check if port is listening
netstat -tulpn | grep :5000

# Test SSL certificate
curl -vI https://your-domain.com:5000/health

# Check webhook server logs
tail -f webhook.log

# Verify Jira can reach webhook
curl -X POST https://your-domain.com:5000/jira-webhook \
  -H "Authorization: Bearer your_secret" \
  -H "Content-Type: application/json" \
  -d '{"webhookEvent":"jira:issue_created","issue":{"key":"TEST-1"}}'
```

## 📚 Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Jira Webhook Security](https://developer.atlassian.com/server/jira/platform/webhooks/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.0.x/security/)
- [SSL Certificate Installation Guide](https://www.ssl.com/how-to/install-ssl-certificate/)

## 🏃‍♂️ Quick Migration from HTTP

If you're currently using the HTTP webhook server:

1. **Stop the HTTP server**
2. **Update your `.env` with SSL settings**
3. **Start the secure server:** `python secure_webhook_server.py`
4. **Update Jira webhook URL** from `http://` to `https://`
5. **Add authentication header** in Jira webhook settings
6. **Test the integration**

This ensures your webhook server meets enterprise security requirements! 🔒 