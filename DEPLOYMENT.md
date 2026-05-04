# AI SAMRAT Production Deployment Guide

This guide will help you deploy the AI SAMRAT content analysis system to a production environment.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least 2GB RAM and 2 CPU cores
- SSL certificate (for HTTPS)
- Domain name (recommended for production)

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-samrat

# Copy environment template
cp .env.example .env

# Edit the environment file
nano .env
```

### 2. Configure Environment Variables

Edit `.env` file with your production settings:

```env
# Application Settings
APP_NAME=AI SAMRAT
ENVIRONMENT=production
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security Settings
SECRET_KEY=your-super-secret-key-change-this-in-production

# CORS Settings
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# SSL Configuration
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

### 3. SSL Certificate Setup

Create the `nginx/ssl` directory and add your SSL certificates:

```bash
mkdir -p nginx/ssl
# Copy your SSL certificates to nginx/ssl/
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

### 4. Deploy the Application

#### Using the Deployment Script (Recommended)

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows:**
```powershell
.\deploy.ps1
```

#### Manual Deployment

```bash
# Build and start services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## 📋 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Application environment |
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Backend port |
| `WORKERS` | `4` | Number of worker processes |
| `MAX_FILE_SIZE` | `209715200` | Max file size (200MB) |
| `SECRET_KEY` | - | JWT secret key |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins |

### Docker Compose Services

- **app**: Main FastAPI application
- **nginx**: Reverse proxy with SSL termination
- **redis**: Caching and session storage

## 🔧 Security Configuration

### 1. SSL/TLS

The application uses HTTPS by default in production. Make sure to:

1. Obtain SSL certificates from a trusted CA
2. Place certificates in `nginx/ssl/`
3. Update nginx configuration with your domain

### 2. Firewall Rules

Open only necessary ports:

```bash
# HTTP (redirects to HTTPS)
sudo ufw allow 80/tcp

# HTTPS
sudo ufw allow 443/tcp

# Backend API (if accessed directly)
sudo ufw allow 8000/tcp
```

### 3. Rate Limiting

Built-in rate limiting is configured:

- API endpoints: 10 requests/minute
- File upload: 2 requests/minute
- Bursts allowed for legitimate traffic

## 📊 Monitoring and Logging

### 1. Application Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f app
docker-compose logs -f nginx
```

### 2. Health Checks

```bash
# Backend health
curl https://yourdomain.com/health

# Metrics (Prometheus format)
curl https://yourdomain.com/metrics
```

### 3. Monitoring Metrics

The application exposes Prometheus metrics:

- HTTP request count and duration
- File upload statistics
- PDF analysis counts
- Error rates

## 🔄 Maintenance

### 1. Updates

```bash
# Pull latest changes
git pull

# Redeploy with latest code
docker-compose up -d --build
```

### 2. Backup

```bash
# Backup data volumes
docker run --rm -v ai-samrat_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
docker run --rm -v ai-samrat_reports:/data -v $(pwd):/backup alpine tar czf /backup/reports-backup.tar.gz -C /data .
```

### 3. Scaling

```bash
# Scale the application
docker-compose up -d --scale app=4
```

## 🚨 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker-compose logs app
   
   # Check resource usage
   docker stats
   ```

2. **SSL certificate errors**
   ```bash
   # Verify certificate paths
   ls -la nginx/ssl/
   
   # Test nginx configuration
   docker-compose exec nginx nginx -t
   ```

3. **High memory usage**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Adjust worker count in .env
   WORKERS=2
   ```

### Performance Optimization

1. **Increase worker processes** based on CPU cores
2. **Enable Redis caching** for repeated analyses
3. **Use CDN** for static assets
4. **Optimize PDF processing** for large files

## 📞 Support

For support and issues:

1. Check the logs first
2. Review this documentation
3. Check GitHub Issues
4. Contact the development team

## 🔒 Security Best Practices

1. **Regular Updates**: Keep Docker images updated
2. **Strong Secrets**: Use long, random secret keys
3. **Network Isolation**: Use Docker networks
4. **Access Control**: Implement authentication if needed
5. **Regular Backups**: Backup data and configurations
6. **Monitoring**: Set up alerts for unusual activity

## 📈 Scaling Considerations

For high-traffic deployments:

1. **Load Balancing**: Use multiple app instances
2. **Database**: Consider PostgreSQL for large-scale data
3. **File Storage**: Use S3 or similar for file storage
4. **CDN**: Use CloudFlare or similar for static content
5. **Monitoring**: Implement comprehensive monitoring

## 🌐 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Load testing performed
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team trained on deployment process
