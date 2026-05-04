# AI SAMRAT Production Deployment Script (PowerShell)
# This script deploys the AI SAMRAT application to production on Windows

param(
    [string]$Version = "latest",
    [string]$Environment = "production"
)

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    White = "White"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

Write-ColorOutput "🚀 Starting AI SAMRAT Deployment" "Green"
Write-ColorOutput "Version: $Version" "Yellow"
Write-ColorOutput "Environment: $Environment" "Yellow"

# Check if Docker is installed
try {
    docker --version > $null 2>&1
    Write-ColorOutput "✅ Docker is installed" "Green"
} catch {
    Write-ColorOutput "❌ Docker is not installed" "Red"
    exit 1
}

# Check if Docker Compose is installed
try {
    docker-compose --version > $null 2>&1
    Write-ColorOutput "✅ Docker Compose is installed" "Green"
} catch {
    Write-ColorOutput "❌ Docker Compose is not installed" "Red"
    exit 1
}

# Create necessary directories
Write-ColorOutput "📁 Creating directories..." "Green"
$Directories = @("logs", "uploads", "reports", "nginx\ssl", "static")
foreach ($dir in $Directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-ColorOutput "  Created: $dir" "Green"
    }
}

# Copy environment file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-ColorOutput "📋 Creating .env file from template..." "Yellow"
    Copy-Item ".env.example" ".env"
    Write-ColorOutput "⚠️  Please edit .env file with your production values!" "Red"
    Write-ColorOutput "⚠️  Especially update SECRET_KEY and domain settings!" "Red"
    Read-Host "Press Enter after editing .env file..."
}

# Build and start services
Write-ColorOutput "🔨 Building Docker images..." "Green"
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "❌ Docker build failed" "Red"
    exit 1
}

Write-ColorOutput "🚢 Starting services..." "Green"
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "❌ Failed to start services" "Red"
    exit 1
}

# Wait for services to be ready
Write-ColorOutput "⏳ Waiting for services to be ready..." "Green"
Start-Sleep -Seconds 30

# Check service health
Write-ColorOutput "🏥 Checking service health..." "Green"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-ColorOutput "✅ Backend is healthy" "Green"
    } else {
        Write-ColorOutput "❌ Backend health check failed" "Red"
        docker-compose logs app
        exit 1
    }
} catch {
    Write-ColorOutput "❌ Backend health check failed" "Red"
    docker-compose logs app
    exit 1
}

# Check if frontend is accessible
try {
    $response = Invoke-WebRequest -Uri "http://localhost/" -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-ColorOutput "✅ Frontend is accessible" "Green"
    } else {
        Write-ColorOutput "⚠️  Frontend might not be ready yet (HTTPS configuration needed)" "Yellow"
    }
} catch {
    Write-ColorOutput "⚠️  Frontend might not be ready yet (HTTPS configuration needed)" "Yellow"
}

# Show running containers
Write-ColorOutput "📊 Running containers:" "Green"
docker-compose ps

# Show logs
Write-ColorOutput "📝 Recent logs:" "Green"
docker-compose logs --tail=20

Write-ColorOutput "🎉 Deployment completed successfully!" "Green"
Write-ColorOutput "📍 Application is running at: http://localhost" "Green"
Write-ColorOutput "📍 Backend API: http://localhost:8000" "Green"
Write-ColorOutput "📍 Health check: http://localhost:8000/health" "Green"

# Show useful commands
Write-ColorOutput "📖 Useful commands:" "Yellow"
Write-Host "  View logs: docker-compose logs -f"
Write-Host "  Stop services: docker-compose down"
Write-Host "  Restart services: docker-compose restart"
Write-Host "  Update application: git pull && docker-compose up -d --build"

Write-ColorOutput "✨ Deployment complete!" "Green"
