# Tech Context: Kubestats

## Technology Stack

### Backend Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI (latest) - High-performance async web framework
- **Database**: PostgreSQL - Relational database with JSON support
- **ORM**: SQLModel - Type-safe SQL interactions with Pydantic integration
- **Task Queue**: Celery with Redis broker - Distributed task processing
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic v2 - Runtime type checking and validation

### Frontend Technologies
- **Language**: TypeScript - Type-safe JavaScript
- **Framework**: React 18 - Component-based UI framework
- **Routing**: TanStack Router - Type-safe routing with nested layouts
- **UI Library**: Chakra UI - Component library with theme support
- **Build Tool**: Vite - Fast development and build tooling
- **API Client**: OpenAPI-generated TypeScript client
- **State Management**: TanStack Query (React Query) - Server state management
- **Testing**: Playwright - End-to-end testing

### Infrastructure & DevOps
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Traefik - Load balancing and SSL termination
- **Development**: mise (formerly rtx) - Runtime version management
- **CI/CD**: GitHub Actions
- **Database Migrations**: Alembic

### External Integrations
- **GitHub API**: Direct API integration via HTTPX
- **Authentication**: GitHub Personal Access Token

## Development Setup

### Environment Management
```bash
# Runtime management with mise
mise install  # Installs Python, Node.js versions from .mise.toml
```

### Backend Setup
```bash
cd backend
uv install  # Python package management with uv
alembic upgrade head  # Database migrations
```

### Frontend Setup
```bash
cd frontend
npm install  # Node.js dependencies
npm run dev  # Development server
```

### Docker Development
```bash
docker-compose up -d  # Full stack with hot reload
```

## Key Dependencies

### Backend Core Dependencies
```toml
# From backend/pyproject.toml
fastapi = "^0.115.4"           # Web framework
sqlmodel = "^0.0.22"           # Database ORM
uvicorn = {extras = ["standard"], version = "^0.32.0"}  # ASGI server
celery = {extras = ["redis"], version = "^5.4.0"}       # Task queue
redis = "^5.2.0"               # Cache and message broker
alembic = "^1.13.3"            # Database migrations
python-jose = {extras = ["cryptography"], version = "^3.3.0"}  # JWT
passlib = {extras = ["bcrypt"], version = "^1.7.4"}     # Password hashing
httpx = "^0.27.0"              # HTTP client for GitHub API
```

### Frontend Core Dependencies
```json
// From frontend/package.json
"@tanstack/react-router": "^1.81.10",     // Routing
"@tanstack/react-query": "^5.59.0",       // Server state management
"@chakra-ui/react": "^2.10.4",            // UI components
"react": "^18.3.1",                       // Core framework
"typescript": "~5.6.3",                   // Type safety
"vite": "^5.4.10",                        // Build tool
"recharts": "^2.12.7"                     // Charts for metrics visualization
```

## Configuration Management

### Environment Variables
```bash
# Backend (.env)
DATABASE_URL=postgresql://postgres:password@localhost/app
SECRET_KEY=your-secret-key
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changethis
GITHUB_TOKEN=your-github-personal-access-token

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

### Docker Configuration
```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://postgres:changethis@db/app
      - GITHUB_TOKEN=${GITHUB_TOKEN}
  
  frontend:
    build: ./frontend
    environment:
      - VITE_API_URL=http://localhost:8000
  
  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=app
      - POSTGRES_PASSWORD=changethis
  
  redis:
    image: redis:7-alpine
```

## Database Schema

### Migration Strategy
- **Alembic**: Handles schema changes with version control
- **Auto-generation**: Models define schema, migrations auto-generated
- **Rollback Support**: All migrations reversible

### Current Schema (Updated)
```sql
-- Core Tables
users (id, email, hashed_password, is_active, is_superuser, full_name)

-- Repository Tables (Updated with sync fields)
repository (
  id, github_id, name, full_name, owner, 
  description, language, topics, license_name, default_branch, 
  sync_status, last_sync_at, sync_error, working_directory_path,
  created_at, discovery_tags, discovered_at
)

repositorymetrics (
  id, repository_id, stars_count, forks_count, watchers_count, 
  open_issues_count, size, updated_at, pushed_at, recorded_at
)

-- Kubernetes Resource Tables (Additional features)
kubernetesresource (
  id, repository_id, source_file_path, resource_type, name, 
  namespace, api_version, kind, content, created_at, updated_at
)
```

## API Design Patterns

### OpenAPI Specification
- **Auto-generated**: FastAPI creates OpenAPI spec from code
- **Type Safety**: Pydantic models ensure request/response validation
- **Documentation**: Interactive docs at `/docs` and `/redoc`

### Response Format
```python
# Consistent response models with enhanced sync tracking
class RepositoryPublic(RepositoryBase):
    id: uuid.UUID
    github_id: int
    discovered_at: datetime
    sync_status: str | None = None
    last_sync_at: datetime | None = None
    sync_error: str | None = None
    working_directory_path: str | None = None
    latest_metrics: RepositoryMetricsPublic | None = None

class RepositoriesPublic(SQLModel):
    data: list[RepositoryPublic]
    count: int
```

### Authentication Flow
```python
# JWT token-based authentication
POST /api/v1/login/access-token
Authorization: Bearer <token>
```

## Task System Architecture

### Celery Configuration
```python
# backend/kubestats/celery_app.py
beat_schedule = {
    "discover-repositories": {
        "task": "kubestats.tasks.discover_repositories.run",
        "schedule": 300.0,  # 5 minutes
    }
}
```

### Task Patterns
```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def discover_repositories(self):
    try:
        # Task implementation with GitHub API integration
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=3)
def sync_repository(self, repository_id: str, create_metrics: bool = False):
    # Repository synchronization task
    pass
```

## GitHub API Integration

### Direct GitHub API Access (Implemented)
- **Client**: Custom HTTPX-based client
- **Endpoints**: Repository search, metadata retrieval, content scanning
- **Authentication**: GitHub Personal Access Token
- **Rate Limiting**: Handled by GitHub's standard rate limits (5000/hour authenticated)

### Current Implementation (Complete)
```python
# backend/kubestats/core/github_client.py
def search_repositories(query: str) -> Dict[str, Any]:
    # Direct GitHub API calls using HTTPX
    # Handles authentication and error cases
    # Returns repository data in GitHub API format

def get_repository_details(owner: str, repo: str) -> Dict[str, Any]:
    # Fetch detailed repository information
    # Include metrics, topics, and metadata

def get_repository_contents(owner: str, repo: str, path: str = "") -> List[Dict]:
    # Fetch repository file contents for scanning
    # Support recursive directory traversal
```

## Frontend Architecture

### Component Structure (Implemented)
```typescript
// Repository Management Components
frontend/src/components/Repositories/
├── Repositories.tsx           // Main repository list with filtering
├── RepositoryDetail.tsx       // Individual repository view
├── MetricsCards.tsx          // Current metrics display
├── MetricsChart.tsx          // Historical metrics visualization
├── RepositoryInfo.tsx        // Repository information display
└── index.ts                  // Component exports

// Routing Structure
frontend/src/routes/_layout/
├── repositories.tsx          // Repository layout route
├── repositories/            
│   ├── index.tsx            // Repository list page
│   └── $repositoryId.tsx    // Repository detail page
```

### State Management Patterns
```typescript
// TanStack Query for server state
const { data: repositories } = useQuery({
  queryKey: ["repositories"],
  queryFn: () => RepositoriesService.repositoriesReadRepositories({}),
})

// React hooks for local state
const [filters, setFilters] = useState<RepositoryFilters>({
  search: "",
  language: "",
  syncStatus: "",
})
```

### UI Component Patterns
```typescript
// Chakra UI component usage
import { Table, Badge, Button, Card } from "@chakra-ui/react"

// Consistent styling patterns
<Badge colorPalette="green">Synced</Badge>
<Button variant="outline" colorPalette="blue">View</Button>
```

## Development Tools

### Code Quality
```bash
# Backend
ruff check .           # Python linting
ruff format .          # Python formatting
mypy .                 # Type checking

# Frontend
npm run lint           # ESLint + TypeScript checking
npm run format         # Prettier formatting
```

### Testing
```bash
# Backend
pytest                 # Unit and integration tests
pytest --cov          # Coverage reporting

# Frontend
npm run test           # Playwright E2E tests
```

## Performance Considerations

### Database Optimization
- **Indexes**: Strategic indexing on frequently queried columns (github_id, sync_status)
- **Connection Pooling**: SQLAlchemy manages connection lifecycle
- **Query Optimization**: Eager loading for related data, efficient pagination

### Caching Strategy
- **Redis**: Task queue and potential response caching
- **Database**: Query result caching for expensive operations
- **Frontend**: TanStack Query handles request caching automatically

### Repository Data Flow
- **Batch Processing**: Efficient bulk operations for repository syncing
- **Incremental Updates**: Only update changed metrics data
- **Background Tasks**: Non-blocking repository discovery and sync operations

## Monitoring and Observability

### Logging
```python
# Structured JSON logging
import structlog
logger = structlog.get_logger()

logger.info("repository_sync_started", repository_id=repo_id)
```

### Metrics
- **Celery Task Metrics**: Success rates, execution times
- **API Response Times**: Endpoint performance monitoring
- **Repository Sync Status**: Track sync success/failure rates

### Health Checks
```python
# API health endpoints
GET /api/health          # Basic service health
GET /api/health/db       # Database connectivity
GET /api/health/redis    # Redis connectivity
```

## Deployment Architecture

### Production Considerations
- **Security**: Environment-based secrets management
- **Scalability**: Horizontal scaling with multiple workers
- **Reliability**: Health checks and graceful shutdown
- **Monitoring**: Log aggregation and error tracking

### Infrastructure Requirements
- **Database**: PostgreSQL 14+ with backup strategy
- **Cache**: Redis for task queue and session storage
- **Compute**: Python 3.11+ runtime with sufficient memory for GitHub API operations
- **Storage**: Persistent volumes for database data and repository content

## Development Constraints

### Technical Constraints
- **Python Version**: 3.11+ required for modern async features
- **Database**: PostgreSQL required for JSON column support
- **Browser Support**: Modern browsers with ES2020+ support
- **GitHub API**: Rate limiting considerations for discovery tasks

### Operational Constraints
- **GitHub API**: Rate limiting (5000/hour authenticated) affects discovery frequency
- **Memory Usage**: Repository content scanning requires careful memory management
- **Network**: External API dependencies require robust error handling

## Future Technical Considerations

### Scalability Enhancements
- **Database Sharding**: Partition by time or repository owner for massive datasets
- **Caching Layer**: Redis Cluster for high availability
- **API Gateway**: Rate limiting and request routing
- **Background Job Scaling**: Multiple Celery workers for parallel processing

### Integration Expansions
- **Multiple Git Hosts**: GitLab, Bitbucket support
- **Real-time Updates**: WebSocket connections for live repository status
- **Analytics**: Time-series database for advanced metrics and trend analysis
- **Kubernetes Integration**: Direct cluster scanning for live resource monitoring

### Performance Optimizations
- **Query Optimization**: Database query performance tuning for large datasets
- **Caching Strategies**: Multi-layer caching for frequently accessed data
- **Batch Processing**: Optimize bulk repository operations
- **Frontend Performance**: Code splitting and lazy loading for large component trees

## Current Implementation Status

### Completed Technology Integration ✅
- **FastAPI Backend**: Full API implementation with OpenAPI generation
- **React Frontend**: Complete repository interface with TanStack Router
- **PostgreSQL**: Database schema with proper migrations and relationships
- **Celery Tasks**: Background job processing for repository operations
- **GitHub API**: Direct integration with HTTPX for repository discovery
- **TypeScript**: Full type safety between frontend and backend
- **Chakra UI**: Consistent design system with responsive components

### Technology Debt and Improvements
- **Monitoring**: Could enhance observability with structured logging
- **Testing**: Could expand test coverage for edge cases
- **Performance**: Could optimize database queries for very large datasets
- **Security**: Could add additional rate limiting and input validation
