# Images

[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success)](https://img.shields.io/badge/status-active-success)

Custom Docker images for personal infrastructure deployment with automated builds and multi-architecture support.

## Quick Start

1. Pull an image: `docker pull ghcr.io/maxexcloo/caddy:latest`
2. Run locally: `docker run -p 80:80 ghcr.io/maxexcloo/caddy:latest`
3. View available tags on GitHub Container Registry

## Features

- **Automated builds**: Triggered by upstream releases
- **Multi-architecture**: Support for linux/amd64 and linux/arm64
- **Enhanced functionality**: Extended upstream images with additional features
- **Release tracking**: Automatic version tracking and updates
- **Version tagging**: Semantic versioning with latest tags

## Installation

Pull images directly from GitHub Container Registry:

```bash
# Pull latest version
docker pull ghcr.io/maxexcloo/caddy:latest
docker pull ghcr.io/maxexcloo/gatus:latest

# Pull specific version
docker pull ghcr.io/maxexcloo/caddy:v2.7.6
```

## Usage

### Available Images

**Caddy** - Enhanced web server with Cloudflare DNS and Docker proxy plugins
```bash
docker run -p 80:80 -p 443:443 ghcr.io/maxexcloo/caddy:latest
```

**Gatus** - Health monitoring service with Tailscale integration
```bash
docker run -p 8080:8080 ghcr.io/maxexcloo/gatus:latest
```

### Repository Structure

Each image directory contains:
- `Dockerfile` - Image build definition
- `REPO` - Upstream repository reference for tracking updates
- `LATEST_RELEASE` - Current version being tracked
- Additional configuration files as needed

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes following the code standards in CLAUDE.md
4. Test image builds locally: `docker build -t test-image ./image-dir`
5. Submit a pull request

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.
