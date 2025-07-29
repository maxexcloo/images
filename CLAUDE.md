# CLAUDE.md - Development Guide

## Project Overview
**Purpose**: Custom Docker images for services with automated builds and releases  
**Status**: Active

## Commands
```bash
# Development
docker build -t image-name ./image-dir    # Build image locally
docker run -it image-name /bin/sh          # Test image

# Build
# Automated via GitHub Actions on push
```

## Tech Stack
- **Language**: Dockerfile
- **Framework**: Docker
- **Testing**: Manual testing with docker run

## Code Standards

### Organization
- **Config/Data**: Alphabetical and recursive (imports, dependencies, object keys)
- **Documentation**: Sort sections, lists, and references alphabetically when logical
- **Files**: Alphabetical in documentation and directories
- **Functions**: Group by purpose, alphabetical within groups
- **Variables**: Alphabetical within scope

### Quality
- **Comments**: Minimal - only for complex business logic
- **Documentation**: Update README.md and docs with every feature change
- **Formatting**: Run formatter before commits
- **KISS principle**: Keep it simple - prefer readable code over clever code
- **Naming**: kebab-case for image names and directories
- **Trailing newlines**: Required in all files

## Project Structure
- **caddy/**: Custom Caddy image with additional modules
- **gatus/**: Custom Gatus monitoring image
- **LATEST_RELEASE**: Release tracking files
- **REPO**: Repository reference files

## Project Specs
- **Automated builds**: GitHub Actions trigger on directory changes
- **Multi-arch support**: Built for linux/amd64 and linux/arm64
- **Release tracking**: LATEST_RELEASE files track current versions
- **Repository links**: REPO files contain upstream repository URLs

## README Guidelines
- **Structure**: Title → Description → Quick Start → Features → Installation → Usage → Contributing
- **Badges**: Include relevant status badges (build, version, license)
- **Code examples**: Always include working examples in code blocks
- **Installation**: Provide copy-paste commands that work
- **Quick Start**: Get users running in under 5 minutes

## Git Workflow
```bash
# After every change
git add . && git commit -m "type: description"

# Always commit after verified working changes
# Keep commits small and focused
```

---

*Simple context for AI assistants working on this open source project.*
