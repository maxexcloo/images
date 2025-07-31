# ARCHITECTURE.md - Technical Design

## Overview

Custom Docker image collection with automated builds and multi-architecture support for personal infrastructure services.

## Core Components

### Image Building
- **Multi-stage builds**: Optimize image size and security through staged construction
- **Multi-architecture**: Support for linux/amd64 and linux/arm64 platforms
- **Base image selection**: Carefully chosen base images for security and size optimization
- **Plugin integration**: Extended functionality through modular plugin architecture

### Automation System
- **Release tracking**: Automated monitoring of upstream repositories for new releases
- **Build triggers**: GitHub Actions workflows triggered by upstream changes
- **Version management**: Semantic versioning with latest and specific version tags
- **Registry publishing**: Automated publishing to GitHub Container Registry

### Service Integration
- **Enhanced functionality**: Extended upstream images with additional plugins and features
- **Configuration management**: Centralized configuration through environment variables
- **Health monitoring**: Built-in health checks and monitoring capabilities
- **Security hardening**: Applied security best practices and minimal attack surface

## Data Flow

1. **Version Detection**: Monitor upstream repositories → Version comparison → Trigger detection
2. **Build Process**: Dockerfile execution → Multi-stage build → Multi-arch compilation → Registry push
3. **Deployment**: Registry pull → Container instantiation → Service startup → Health verification

## Key Features

### Caddy Image
- **DNS Challenge**: Cloudflare DNS plugin for automatic SSL certificate generation
- **Docker Proxy**: Docker container discovery and automatic proxy configuration
- **Performance**: Optimized configuration for high-performance web serving
- **Security**: Enhanced security headers and configuration

### Gatus Image
- **Tailscale Integration**: VPN connectivity for secure monitoring across networks
- **Health Monitoring**: Comprehensive service health checking and alerting
- **Supervisor Management**: Process supervision for reliable service operation
- **Multi-service**: Combined Gatus and Tailscale services in single container

## Technology Stack

### Build System
- **Docker**: Multi-stage containerization platform
- **GitHub Actions**: Continuous integration and deployment
- **QEMU**: Multi-architecture emulation for cross-platform builds
- **Buildx**: Docker build enhancement for advanced features

### Runtime
- **Alpine Linux**: Minimal base images for security and size optimization
- **Supervisor**: Process management for multi-service containers
- **Health Checks**: Container health monitoring and automatic recovery

---

*Technical architecture documentation for the images project.*
