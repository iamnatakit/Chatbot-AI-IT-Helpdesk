# Docker Setup - Frontend Updates

## 🐳 Docker Build & Run

The frontend Docker setup has been updated to support the new React Router pages.

### Build and Run with Docker Compose

```bash
docker-compose up --build
```

This will:
- Build the backend service (port 8000)
- Build the frontend service (port 3000)
- Both services will restart automatically if they crash

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:3000/health

## 📦 What's New in Docker

### Frontend Dockerfile Changes
✅ Added `.npmrc` copy for `legacy-peer-deps` support
✅ Multi-stage build for optimized image size
✅ Nginx as reverse proxy for production

### New Nginx Configuration
✅ React Router support with SPA routing
✅ Static asset caching (1 year for hashed files)
✅ Gzip compression enabled
✅ Health check endpoint included

### Key Files

- **frontend/Dockerfile** - Multi-stage build process
- **frontend/nginx.conf** - Nginx configuration for SPA
- **frontend/.npmrc** - NPM legacy peer deps configuration
- **docker-compose.yml** - Service orchestration

## 🔧 Development vs Production

### Local Development
```bash
cd frontend
npm install
npm run dev
```
Runs on http://localhost:5173 with hot reloading

### Docker Production
```bash
docker-compose up --build
```
Runs on http://localhost:3000 with Nginx

## 📋 Pages Available (After Installation)

Navigate using the sidebar:
- 🏠 Chat (Main page)
- 📋 Compliance Agent
- 🔢 Token Monitor  
- 💰 Cost Monitor
- 📑 Billing History
- ⚡ Response Monitor

## ⚠️ Troubleshooting

**Port 3000 already in use:**
```bash
docker-compose down  # Stop all containers
docker-compose up --build
```

**Build fails with npm error:**
The `.npmrc` file handles dependency conflicts. If issues persist:
```bash
docker-compose down
rm -rf frontend/node_modules
docker-compose up --build
```

**Pages not routing correctly:**
Make sure `nginx.conf` is in the frontend root directory.
