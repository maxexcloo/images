# Images

Custom Docker images for personal infrastructure deployment.

## Overview

This repository contains Docker image definitions organized as individual directories. Each directory represents a separate image build with its own Dockerfile and configuration files. Images are automatically built and published when upstream dependencies release new versions.

## Repository Structure

Each image directory contains:
- `Dockerfile` - Image build definition
- `REPO` - Upstream repository reference for tracking updates
- `LATEST_RELEASE` - Current version being tracked
- Additional configuration files as needed (e.g., `supervisord.conf`)

## Automation

A GitHub Actions workflow automatically:
- Monitors upstream repositories for new releases using the `REPO` file
- Builds multi-platform Docker images (amd64/arm64) when updates are detected
- Publishes images to GitHub Container Registry with version tags
- Updates the `LATEST_RELEASE` file to track current versions
- Runs daily and can be triggered manually

## Current Images

**Caddy** - Enhanced web server with Cloudflare DNS and Docker proxy plugins for automated certificate management and service discovery.

**Gatus** - Health monitoring service integrated with Tailscale for secure mesh networking and multi-process supervision.

## Dependencies

Images integrate with external services including Cloudflare (DNS/certificates), Tailscale (networking), and Fly.io (hosting platform), while extending upstream projects like Caddy and Gatus with additional functionality.
