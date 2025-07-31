# CLAUDE.md - Development Guide

## Project Overview
**Purpose**: Custom Docker images for services with automated builds and multi-architecture support
**Status**: Active
**Language**: Dockerfile

## Code Standards

### Organization
- **Config/Data**: Alphabetical and recursive (imports, dependencies, object keys, mise tasks)
- **Documentation**: Sort sections, lists, and references alphabetically when logical
- **Files**: Alphabetical in documentation and directories
- **Functions**: Group by purpose, alphabetical within groups
- **Variables**: Alphabetical within scope

### Quality
- **Comments**: Minimal - only for complex business logic
- **Documentation**: Update ARCHITECTURE.md and README.md with every feature change
- **Error handling**: Graceful container failure with meaningful exit codes
- **Formatting**: Run `mise run fmt` before commits
- **KISS principle**: Keep it simple - prefer readable code over clever code
- **Naming**: kebab-case for image names and directories
- **Testing**: Manual testing with docker build and run
- **Trailing newlines**: Required in all files

## Commands
```bash
# Build
mise run build           # Build all Docker images

# Development
mise run dev             # Development validation cycle

# Format
mise run fmt             # Format Dockerfile and config files

# Check
mise run check           # All validation (fmt + build + test)

# Test
mise run test            # Test all Docker images
```

## Development Guidelines

### Contribution Standards
- **Code Changes**: Follow sorting rules and maintain Docker best practices
- **Documentation**: Keep all docs synchronized and cross-referenced
- **Feature Changes**: Update README.md and ARCHITECTURE.md when adding features

### Documentation Structure
- **ARCHITECTURE.md**: Technical design and implementation details
- **CLAUDE.md**: Development standards and project guidelines
- **README.md**: Tool overview and usage guide

## Container Interface Standards
- **Clear responses**: Provide meaningful HTTP status codes and error messages
- **Consistent ports**: Use standard ports for services where applicable
- **Error messages**: Include container context and timestamps in logs
- **Health checks**: Always include health endpoints where applicable

## Development Workflow Standards

### Environment Management
- Use **mise** for consistent development environments
- Define common tasks as mise scripts in `.mise.toml`
- Pin tool versions in `.mise.toml`

## Error Handling Standards
- **Contextual errors**: Include container and service context in logs
- **Graceful degradation**: Handle upstream service failures gracefully
- **Informative messages**: Clear error responses for debugging
- **User-friendly output**: Meaningful exit codes and error messages

### Required Development Tasks
- **build**: Build all Docker images
- **check**: All validation (fmt + build + test)
- **dev**: Development validation cycle
- **fmt**: Format Dockerfile and config files
- **test**: Test all Docker images

## Project Structure
- **caddy/**: Enhanced Caddy web server with Cloudflare DNS and Docker proxy plugins
- **gatus/**: Health monitoring service with Tailscale integration
- ***/Dockerfile**: Multi-stage Docker build definitions
- ***/LATEST_RELEASE**: Version tracking for automated updates
- ***/REPO**: Upstream repository references

## README Guidelines
- **Badges**: Include relevant status badges (license, status, docker, language)
- **Code examples**: Always include working examples in code blocks
- **Installation**: Provide copy-paste commands that work
- **Quick Start**: Get users running in under 5 minutes
- **Structure**: Title → Badges → Description → Quick Start → Features → Installation → Usage → Contributing

## Tech Stack
- **Backend**: Docker multi-stage builds
- **CI/CD**: GitHub Actions with multi-architecture support
- **Registry**: GitHub Container Registry (ghcr.io)
- **Testing**: Manual testing with docker build and run

---

*Development guide for the images open source project.*
