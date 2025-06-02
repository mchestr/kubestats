# Kubestats

**Kubernetes Ecosystem Discovery & Analytics Platform**

Kubestats is a comprehensive platform for discovering, tracking, and analyzing GitHub repositories in the Kubernetes and container ecosystem. Built on FastAPI, it automatically discovers repositories with Kubernetes-related topics and provides time-series analytics to understand ecosystem trends and project health.

## 🎯 What is Kubestats?

Kubestats solves the challenge of discovering and tracking the vast, rapidly-evolving Kubernetes ecosystem. It automatically discovers GitHub repositories with Kubernetes-related topics (`kubesearch`, `k8s-at-home`) and provides:

- **📊 Ecosystem Analytics**: Historical trends and statistics across the Kubernetes community
- **🔍 Smart Discovery**: Automated repository discovery with topic-based filtering  
- **📈 Growth Tracking**: Time-series metrics for stars, forks, issues, and activity
- **🔬 Trend Analysis**: Identify emerging tools and declining projects
- **⚡ Real-time Updates**: Background tasks keep data fresh and current

Whether you're a developer seeking the right Kubernetes tools, a maintainer benchmarking your project, or a researcher analyzing ecosystem health, Kubestats provides the insights you need.

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
    - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
    - 🔄 [Celery](https://docs.celeryq.dev/) with Redis for background task processing.
    - 🐙 Direct GitHub API integration via HTTPX for repository discovery.
- 🚀 [React](https://react.dev) for the frontend.
    - 💃 Using TypeScript, hooks, Vite, and other parts of a modern frontend stack.
    - 🎨 [Chakra UI](https://chakra-ui.com) for the frontend components.
    - 🤖 An automatically generated frontend client from OpenAPI spec.
    - 📊 [TanStack Query](https://tanstack.com/query) for efficient server state management.
    - 🧪 [Playwright](https://playwright.dev) for End-to-End testing.
    - 🦇 Dark mode support.
- 🐋 [Docker Compose](https://www.docker.com) for development and production.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email based password recovery.
- ✅ Tests with [Pytest](https://pytest.org).
- 📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
- 🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates.
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

### Repository Discovery Dashboard

[![Repository Discovery](img/discovery.png)](https://github.com/mchestr/kubestats)

### Ecosystem Analytics

[![Analytics Dashboard](img/analytics.png)](https://github.com/mchestr/kubestats)

### Trend Analysis

[![Trend Charts](img/trends.png)](https://github.com/mchestr/kubestats)

### Repository Details

[![Repository Details](img/repository.png)](https://github.com/mchestr/kubestats)

### Interactive API Documentation

[![API docs](img/docs.png)](https://github.com/mchestr/kubestats)

## Docker Images

Pre-built Docker images are automatically published to GitHub Container Registry (GHCR) on every release:

- **Backend**: `ghcr.io/mchestr/kubestats-backend:latest`
- **Frontend**: `ghcr.io/mchestr/kubestats-frontend:latest`

### Using Published Images

You can use the published images directly with Docker Compose:

```yaml
# docker-compose.prod.yml
services:
  backend:
    image: ghcr.io/mchestr/kubestats-backend:latest
    # ... your configuration
  
  frontend:
    image: ghcr.io/mchestr/kubestats-frontend:latest
    # ... your configuration
```

### Available Tags

- `latest` - Latest stable release from main branch
- `v*` - Specific version tags (e.g., `v1.0.0`)
- `main` - Latest build from main branch
- `develop` - Latest build from develop branch

### Quick Production Deployment

```bash
# Using published images
docker-compose -f docker-compose.prod.yml up -d

# Using specific version
TAG=v1.0.0 docker-compose -f docker-compose.prod.yml up -d
```

## How To Use It

You can **just fork or clone** this repository and use it as is.

✨ It just works. ✨

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/mchestr/kubestats.git
cd kubestats

# Start all services
docker-compose up -d

# Access the application
open http://localhost
```

The application will automatically:
- Set up PostgreSQL database with initial schema
- Start the FastAPI backend with GitHub API integration
- Launch the React frontend with Chakra UI
- Begin discovering Kubernetes repositories in the background

### Environment Setup with mise

Kubestats uses [mise](https://mise.jdx.dev/) for runtime management:

```bash
# Install required runtimes
mise install

# Run all setup tasks
mise run setup
```

### How to Use a Private Repository

If you want to have a private repository, GitHub won't allow you to simply fork it as it doesn't allow changing the visibility of forks.

But you can do the following:

- Create a new GitHub repo, for example `my-kubestats`.
- Clone this repository manually, set the name with the name of the project you want to use, for example `my-kubestats`:

```bash
git clone git@github.com:mchestr/kubestats.git my-kubestats
```

- Enter into the new directory:

```bash
cd my-kubestats
```

- Set the new origin to your new repository, copy it from the GitHub interface, for example:

```bash
git remote set-url origin git@github.com:octocat/my-kubestats.git
```

- Add this repo as another "remote" to allow you to get updates later:

```bash
git remote add upstream git@github.com:mchestr/kubestats.git
```

- Push the code to your new repository:

```bash
git push -u origin master
```

### Update From the Original Template

After cloning the repository, and after doing changes, you might want to get the latest changes from this original template.

- Make sure you added the original repository as a remote, you can check it with:

```bash
git remote -v

origin    git@github.com:octocat/my-kubestats.git (fetch)
origin    git@github.com:octocat/my-kubestats.git (push)
upstream    git@github.com:mchestr/kubestats.git (fetch)
upstream    git@github.com:mchestr/kubestats.git (push)
```

- Pull the latest changes without merging:

```bash
git pull --no-commit upstream main
```

This will download the latest changes from this template without committing them, that way you can check everything is right before committing.

- If there are conflicts, solve them in your editor.

- Once you are done, commit the changes:

```bash
git merge --continue
```

### Configure

You can then update configs in the `.env` files to customize your configurations.

Before deploying it, make sure you change at least the values for:

- `SECRET_KEY`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`
- `GITHUB_TOKEN` (required for repository discovery)

You can (and should) pass these as environment variables from secrets.

Read the [deployment.md](./deployment.md) docs for more details.

### Generate Secret Keys

Some environment variables in the `.env` file have a default value of `changethis`.

You have to change them with a secret key, to generate secret keys you can run the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the content and use that as password / secret key. And run that again to generate another secure key.

## Repository Discovery

Kubestats automatically discovers GitHub repositories tagged with specific Kubernetes-related topics:

- `kubesearch` - General Kubernetes tools and utilities
- `k8s-at-home` - Home lab and self-hosted Kubernetes projects

### Adding Your Repository

To have your repository discovered by Kubestats:

1. Add one of the supported topics to your GitHub repository
2. Ensure your repository is public
3. Wait for the next discovery cycle (runs periodically via Celery tasks)

### Discovery Metrics

For each discovered repository, Kubestats tracks:

- ⭐ **Stars**: Community interest and adoption
- 🍴 **Forks**: Developer engagement and contributions  
- 🐛 **Issues**: Project activity and health
- 📝 **Commits**: Development activity over time
- 🏷️ **Languages**: Technology stack analysis
- 📅 **Created/Updated**: Project age and freshness

## Development Environment

### Prerequisites

- [mise](https://mise.jdx.dev/) for runtime management
- Docker and Docker Compose
- GitHub Personal Access Token (for API access)

### Setup

```bash
# Install mise (if not already installed)
curl https://mise.run | sh

# Clone and setup
git clone https://github.com/mchestr/kubestats.git
cd kubestats

# Install runtimes and dependencies
mise install
mise run setup

# Configure environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit .env files with your configuration
```

### Running Locally

```bash
# Start all services with Docker Compose
mise run dev

# Or start individual services
mise run backend:dev  # FastAPI backend
mise run frontend:dev # React frontend  
mise run celery:dev   # Background tasks
```

## How To Use It - Alternative With Copier

This repository also supports generating a new project using [Copier](https://copier.readthedocs.io).

It will copy all the files, ask you configuration questions, and update the `.env` files with your answers.

### Install Copier

You can install Copier with:

```bash
pip install copier
```

Or better, if you have [`pipx`](https://pipx.pypa.io/), you can run it with:

```bash
pipx install copier
```

**Note**: If you have `pipx`, installing copier is optional, you could run it directly.

### Generate a Project With Copier

Decide a name for your new project's directory, you will use it below. For example, `my-kubestats-fork`.

Go to the directory that will be the parent of your project, and run the command with your project's name:

```bash
copier copy https://github.com/mchestr/kubestats my-kubestats-fork --trust
```

If you have `pipx` and you didn't install `copier`, you can run it directly:

```bash
pipx run copier copy https://github.com/mchestr/kubestats my-kubestats-fork --trust
```

**Note** the `--trust` option is necessary to be able to execute a [post-creation script](https://github.com/mchestr/kubestats/blob/master/.copier/update_dotenv.py) that updates your `.env` files.

### Input Variables

Copier will ask you for some data, you might want to have at hand before generating the project.

But don't worry, you can just update any of that in the `.env` files afterwards.

The input variables, with their default values (some auto generated) are:

- `project_name`: (default: `"Kubestats"`) The name of the project, shown to users (in .env).
- `stack_name`: (default: `"kubestats"`) The name of the stack used for Docker Compose labels and project name (no spaces, no periods) (in .env).
- `secret_key`: (default: `"changethis"`) The secret key for the project, used for security, stored in .env, you can generate one with the method above.
- `first_superuser`: (default: `"admin@example.com"`) The email of the first superuser (in .env).
- `first_superuser_password`: (default: `"changethis"`) The password of the first superuser (in .env).
- `github_token`: (default: `"changethis"`) GitHub Personal Access Token for repository discovery (in .env).
- `smtp_host`: (default: "") The SMTP server host to send emails, you can set it later in .env.
- `smtp_user`: (default: "") The SMTP server user to send emails, you can set it later in .env.
- `smtp_password`: (default: "") The SMTP server password to send emails, you can set it later in .env.
- `emails_from_email`: (default: `"info@example.com"`) The email account to send emails from, you can set it later in .env.
- `postgres_password`: (default: `"changethis"`) The password for the PostgreSQL database, stored in .env, you can generate one with the method above.
- `sentry_dsn`: (default: "") The DSN for Sentry, if you are using it, you can set it later in .env.

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

### Key Backend Features

- **Repository Discovery**: Automated GitHub API integration for finding Kubernetes repositories
- **Time-Series Storage**: Efficient storage and querying of repository metrics over time
- **Background Tasks**: Celery-powered asynchronous processing for discovery and updates
- **REST API**: Comprehensive endpoints for repository data, analytics, and trends
- **Authentication**: JWT-based auth with user management for accessing advanced features

### API Endpoints

The backend provides several key endpoint groups:

- `/api/v1/repositories/` - Repository CRUD and search operations
- `/api/v1/analytics/` - Ecosystem analytics and trend data
- `/api/v1/discovery/` - Repository discovery management
- `/api/v1/metrics/` - Time-series metrics and statistics

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

### Key Frontend Features

- **Repository Explorer**: Browse and search discovered Kubernetes repositories
- **Analytics Dashboard**: Visualize ecosystem trends and repository growth
- **Trend Analysis**: Interactive charts showing metrics over time
- **Repository Details**: Comprehensive view of individual repository data
- **Responsive Design**: Mobile-first design with Chakra UI components

### Development Commands

```bash
# Start frontend development server
mise run frontend:dev

# Generate API client from OpenAPI spec
mise run generate-client

# Run frontend tests
mise run frontend:test

# Run linting and formatting
mise run frontend:lint
```

## Deployment

Deployment docs: [deployment.md](./deployment.md).

### Production Deployment with Docker Images

The fastest way to deploy Kubestats is using the pre-built Docker images:

```bash
# Download production compose file
curl -O https://raw.githubusercontent.com/mchestr/kubestats/main/docker-compose.prod.yml

# Configure environment
export SECRET_KEY="your-secret-key"
export POSTGRES_PASSWORD="your-db-password"
export GITHUB_TOKEN="your-github-token"
export FIRST_SUPERUSER_PASSWORD="your-admin-password"

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Required environment variables for production:

- `GITHUB_TOKEN` - GitHub Personal Access Token for API access
- `SECRET_KEY` - Application secret key (generate with Python secrets)
- `POSTGRES_PASSWORD` - Database password
- `FIRST_SUPERUSER_PASSWORD` - Initial admin user password

Optional variables:

- `DISCOVERY_TOPICS` - Comma-separated list of GitHub topics to discover (default: "kubesearch,k8s-at-home")
- `DISCOVERY_INTERVAL` - How often to run discovery in seconds (default: 3600)
- `SENTRY_DSN` - Sentry error tracking DSN

## Development

General development docs: [development.md](./development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.

### Development Workflow

```bash
# Setup development environment
mise install
mise run setup

# Start all services for development
mise run dev

# Run tests
mise run test

# Format and lint code
mise run format
mise run lint

# Database operations
mise run db:migrate    # Run database migrations
mise run db:upgrade    # Upgrade to latest schema
mise run db:reset      # Reset database (development only)

# Background tasks
mise run celery:dev    # Start Celery worker
mise run celery:beat   # Start Celery scheduler
mise run celery:flower # Start Celery monitoring UI
```

### Project Structure

```
kubestats/
├── backend/              # FastAPI Python backend
│   ├── kubestats/        # Main application package
│   │   ├── api/          # API route handlers
│   │   ├── core/         # Core configuration and security
│   │   ├── models.py     # SQLModel database models
│   │   ├── crud.py       # Database operations
│   │   ├── tasks/        # Celery background tasks
│   │   └── tests/        # Backend test suite
│   └── alembic/          # Database migrations
├── frontend/             # React TypeScript frontend
│   ├── src/              # Frontend source code
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Application pages
│   │   ├── hooks/        # Custom React hooks
│   │   └── client/       # Generated API client
│   └── tests/            # Frontend test suite
├── data/                 # Repository data storage
│   └── repos/            # Discovered repository data
└── memory-bank/          # Project documentation and context
```

## Architecture

### Data Flow

1. **Discovery**: Celery tasks periodically query GitHub API for repositories with target topics
2. **Storage**: Repository metadata and metrics stored in PostgreSQL with time-series tables
3. **Processing**: Background tasks calculate trends, analytics, and derived metrics
4. **API**: FastAPI exposes REST endpoints for frontend and external consumers
5. **Frontend**: React app provides interactive dashboards and repository exploration

### Key Components

- **GitHub API Client**: HTTPX-based client for repository discovery and metrics collection
- **Celery Workers**: Background processing for discovery, metrics updates, and analytics
- **PostgreSQL**: Primary data store with time-series tables for metrics tracking
- **Redis**: Message broker for Celery and caching layer
- **FastAPI**: High-performance async API server with automatic OpenAPI documentation
- **React Frontend**: Modern TypeScript UI with Chakra UI components and TanStack Query

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Run the test suite (`mise run test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Coding Standards

- **Backend**: Follow PEP 8, use type hints, write docstrings
- **Frontend**: Use TypeScript strict mode, follow React best practices
- **Testing**: Maintain test coverage above 80%
- **Documentation**: Update relevant docs for new features

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

Kubestats is licensed under the terms of the MIT license.
