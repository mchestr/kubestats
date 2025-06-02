# Tech Context: Kubestats

## Technology Stack

### Backend Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI (latest) - High-performance async web framework
- **Database**: PostgreSQL - Relational database with JSON support and advanced indexing
- **ORM**: SQLModel - Type-safe SQL interactions with Pydantic integration
- **Task Queue**: Celery with Redis broker - Distributed task processing for sync and scanning
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic v2 - Runtime type checking and validation
- **YAML Processing**: PyYAML - YAML parsing for Kubernetes resource scanning
- **File Operations**: Hashlib - File hash-based change detection

### Frontend Technologies
- **Language**: TypeScript - Type-safe JavaScript
- **Framework**: React 18 - Component-based UI framework
- **Routing**: TanStack Router - Type-safe routing with nested layouts
- **UI Library**: Chakra UI - Component library with theme support and enhanced analytics components
- **Build Tool**: Vite - Fast development and build tooling
- **API Client**: OpenAPI-generated TypeScript client with resource and event types
- **State Management**: TanStack Query (React Query) - Server state management with real-time updates
- **Charts**: Recharts - Interactive charts for resource event analytics
- **Testing**: Playwright - End-to-end testing

### Infrastructure & DevOps
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Traefik - Load balancing and SSL termination
- **Development**: mise (formerly rtx) - Runtime version management
- **CI/CD**: GitHub Actions
- **Database Migrations**: Alembic with enhanced schema for resources and events

### External Integrations
- **GitHub API**: Direct API integration via HTTPX with content access for YAML scanning
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
alembic upgrade head  # Database migrations including resource schemas
```

### Frontend Setup
```bash
cd frontend
npm install  # Node.js dependencies including analytics libraries
npm run dev  # Development server with resource analytics
```

### Docker Development
```bash
docker-compose up -d  # Full stack with hot reload and scanning capabilities
```

## Key Dependencies

### Backend Core Dependencies
```toml
# From backend/pyproject.toml
fastapi = "^0.115.4"           # Web framework
sqlmodel = "^0.0.22"           # Database ORM with enhanced models
uvicorn = {extras = ["standard"], version = "^0.32.0"}  # ASGI server
celery = {extras = ["redis"], version = "^5.4.0"}       # Task queue for scanning
redis = "^5.2.0"               # Cache and message broker
alembic = "^1.13.3"            # Database migrations
python-jose = {extras = ["cryptography"], version = "^3.3.0"}  # JWT
passlib = {extras = ["bcrypt"], version = "^1.7.4"}     # Password hashing
httpx = "^0.27.0"              # HTTP client for GitHub API and content access
pyyaml = "^6.0.1"              # YAML parsing for resource scanning
structlog = "^23.1.0"          # Structured logging for scanning operations
```

### Frontend Core Dependencies
```json
// From frontend/package.json
"@tanstack/react-router": "^1.81.10",     // Routing with resource analytics routes
"@tanstack/react-query": "^5.59.0",       // Server state management with event updates
"@chakra-ui/react": "^2.10.4",            // UI components with enhanced analytics
"react": "^18.3.1",                       // Core framework
"typescript": "~5.6.3",                   // Type safety with resource types
"vite": "^5.4.10",                        // Build tool
"recharts": "^2.12.7",                    // Charts for event analytics and trends
"react-icons": "^4.12.0"                  // Icons for resource and event UI
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
      - CELERY_BROKER_URL=redis://redis:6379/0
  
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
  
  celery:
    build: ./backend
    command: celery -A kubestats.celery_app worker --loglevel=info
    depends_on:
      - redis
      - db
```

## Database Schema

### Migration Strategy
- **Alembic**: Handles schema changes with version control
- **Auto-generation**: Models define schema, migrations auto-generated
- **Rollback Support**: All migrations reversible
- **Performance Optimization**: Strategic indexing for resource and event queries

### Enhanced Schema (Updated)
```sql
-- Core Tables
users (id, email, hashed_password, is_active, is_superuser, full_name)

-- Enhanced Repository Tables with Scanning
repository (
  id, github_id, name, full_name, owner, 
  description, language, topics, license_name, default_branch, 
  sync_status, last_sync_at, sync_error, working_directory_path,
  scan_status, last_scan_at, scan_error,  -- NEW: Scanning status tracking
  last_scan_total_resources,               -- NEW: Resource count tracking
  created_at, discovery_tags, discovered_at
)

repositorymetrics (
  id, repository_id, stars_count, forks_count, watchers_count, 
  open_issues_count, size, 
  kubernetes_resources_count,              -- NEW: K8s resource count
  updated_at, pushed_at, recorded_at
)

-- NEW: Kubernetes Resource Tables
kubernetesresource (
  id, repository_id, api_version, kind, name, 
  namespace, file_path, file_hash, version, data, 
  status, deleted_at, created_at, updated_at
)

kubernetesresourceevent (
  id, resource_id, repository_id, event_type, event_timestamp,
  resource_name, resource_namespace, resource_kind, resource_api_version,
  file_path, file_hash_before, file_hash_after, changes_detected,
  resource_data, sync_run_id
)

-- Performance Indexes
CREATE INDEX idx_kubernetesresource_repo_status ON kubernetesresource(repository_id, status);
CREATE INDEX idx_kubernetesresourceevent_repo_timestamp ON kubernetesresourceevent(repository_id, event_timestamp DESC);
CREATE INDEX idx_kubernetesresourceevent_type_timestamp ON kubernetesresourceevent(event_type, event_timestamp DESC);
```

## API Design Patterns

### OpenAPI Specification
- **Auto-generated**: FastAPI creates OpenAPI spec from code including resource endpoints
- **Type Safety**: Pydantic models ensure request/response validation for all resource operations
- **Documentation**: Interactive docs at `/docs` and `/redoc` with resource analytics examples

### Enhanced Response Format
```python
# Enhanced response models with resource and event data
class RepositoryPublic(RepositoryBase):
    id: uuid.UUID
    github_id: int
    discovered_at: datetime
    sync_status: str | None = None
    last_sync_at: datetime | None = None
    sync_error: str | None = None
    scan_status: str | None = None          # NEW: Scan status
    last_scan_at: datetime | None = None    # NEW: Last scan timestamp
    scan_error: str | None = None           # NEW: Scan error tracking
    last_scan_total_resources: int | None = None  # NEW: Resource count
    working_directory_path: str | None = None
    latest_metrics: RepositoryMetricsPublic | None = None

class KubernetesResourceEventPublic(SQLModel):  # NEW
    id: uuid.UUID
    event_type: str
    event_timestamp: datetime
    resource_name: str
    resource_namespace: str | None
    resource_kind: str
    file_path: str
    changes_detected: list[str]
    sync_run_id: uuid.UUID

class KubernetesResourceEventsPublic(SQLModel):  # NEW
    data: list[KubernetesResourceEventPublic]
    count: int
```

### Authentication Flow
```python
# JWT token-based authentication (unchanged)
POST /api/v1/login/access-token
Authorization: Bearer <token>
```

## Task System Architecture

### Enhanced Celery Configuration
```python
# backend/kubestats/celery_app.py
beat_schedule = {
    "discover-repositories": {
        "task": "kubestats.tasks.discover_repositories.run",
        "schedule": 300.0,  # 5 minutes
    },
    "sync-repositories": {
        "task": "kubestats.tasks.sync_repositories.sync_all_repositories",
        "schedule": 900.0,  # 15 minutes
    },
    "scan-repositories": {                    # NEW: Resource scanning
        "task": "kubestats.tasks.scan_repositories.scan_all_repositories", 
        "schedule": 1800.0,  # 30 minutes
    }
}
```

### Enhanced Task Patterns
```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def discover_repositories(self):
    try:
        # Task implementation with GitHub API integration
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task(bind=True, max_retries=3)
def sync_repository(self, repository_id: str, create_metrics: bool = False):
    # Repository synchronization task
    pass

@shared_task(bind=True, max_retries=3)  # NEW
def scan_repository(self, repository_id: str) -> dict:
    # Resource scanning task with change detection
    # File hash comparison for change detection
    # Event generation for resource lifecycle changes
    pass
```

## GitHub API Integration

### Enhanced GitHub API Access (Implemented)
- **Client**: Custom HTTPX-based client with content access
- **Endpoints**: Repository search, metadata retrieval, content scanning, file access
- **Authentication**: GitHub Personal Access Token
- **Rate Limiting**: Handled by GitHub's standard rate limits (5000/hour authenticated)
- **Content Access**: Repository file content retrieval for YAML scanning

### Enhanced Implementation (Complete)
```python
# backend/kubestats/core/github_client.py
def search_repositories(query: str) -> Dict[str, Any]:
    # Direct GitHub API calls using HTTPX
    # Handles authentication and error cases
    # Returns repository data in GitHub API format

def get_repository_details(owner: str, repo: str) -> Dict[str, Any]:
    # Fetch detailed repository information
    # Include metrics, topics, and metadata

def get_repository_contents(owner: str, repo: str, path: str = "") -> List[Dict]:  # ENHANCED
    # Fetch repository file contents for scanning
    # Support recursive directory traversal
    # Return file content and metadata for YAML parsing

def get_file_content(owner: str, repo: str, path: str) -> str:  # NEW
    # Fetch individual file content for YAML scanning
    # Handle encoding and decode file content
    # Support for all text file types
```

## YAML Scanner Architecture

### Scanner Framework (New Component)
```python
# backend/kubestats/core/yaml_scanner/
├── repository_scanner.py      # Main scanning orchestration
├── resource_db_service.py     # Database operations for resources
├── models.py                  # Scanner data models
└── resource_scanners/
    ├── __init__.py           # Scanner registry
    └── flux/                 # Flux-specific scanners
        ├── git_repository.py
        ├── kustomization.py
        ├── helm_release.py
        └── oci_repository.py
```

### Scanner Implementation Patterns
```python
# Modular scanner architecture
class ResourceScanner:
    def can_handle(self, resource_data: dict) -> bool:
        # Determine if scanner can handle this resource type
        pass
    
    def extract_data(self, resource_data: dict, file_path: str) -> ResourceData:
        # Extract structured data from YAML resource
        # Return ResourceData with all necessary fields
        pass

# Change detection pattern
def detect_changes(current_resources: List[ResourceData], 
                  existing_resources: List[KubernetesResource]) -> ChangeSet:
    # File hash-based change detection
    # Generate CREATED, MODIFIED, DELETED events
    # Return comprehensive change set
    pass
```

## Frontend Architecture

### Enhanced Component Structure (Implemented)
```typescript
// Enhanced Repository Management Components
frontend/src/components/Repositories/
├── Repositories.tsx           // Main repository list with scan status
├── RepositoryDetail.tsx       // Individual repository view with resource analytics
├── MetricsCards.tsx          // Current metrics display with resource counts
├── MetricsChart.tsx          // Historical metrics visualization
├── RepositoryInfo.tsx        // Repository information with scan status
├── RepositoryEventsTable.tsx // NEW: Resource lifecycle event table
├── RepositoryEventsChart.tsx // NEW: Event trend visualization
└── index.ts                  // Component exports

// Enhanced Routing Structure
frontend/src/routes/_layout/
├── repositories.tsx          // Repository layout route
├── repositories/            
│   ├── index.tsx            // Repository list page with scan status
│   └── $repositoryId.tsx    // Repository detail page with event analytics
```

### Enhanced State Management Patterns
```typescript
// TanStack Query for server state with resource events
const { data: repositories } = useQuery({
  queryKey: ["repositories"],
  queryFn: () => RepositoriesService.repositoriesReadRepositories({}),
})

const { data: events } = useQuery({  // NEW: Event analytics
  queryKey: ["repository-events", repositoryId, filters],
  queryFn: () => RepositoriesService.repositoriesReadRepositoryEvents({
    path: { repository_id: repositoryId },
    query: { event_type: filters.eventType, resource_kind: filters.resourceKind }
  }),
})

// React hooks for local state with enhanced filtering
const [filters, setFilters] = useState<RepositoryFilters>({
  search: "",
  language: "",
  syncStatus: "",
  scanStatus: "",           // NEW: Scan status filter
})

const [eventFilters, setEventFilters] = useState({  // NEW: Event filtering
  eventType: "",
  resourceKind: "",
  namespace: "",
})
```

### Enhanced UI Component Patterns
```typescript
// Chakra UI component usage with resource analytics
import { Table, Badge, Button, Card, Grid } from "@chakra-ui/react"

// Enhanced styling patterns with resource status
<Badge colorPalette="green">Scanned</Badge>
<Badge colorPalette="blue">Scanning</Badge>
<Badge colorPalette="red">Scan Error</Badge>
<Button variant="outline" colorPalette="blue">Scan Repository</Button>

// Resource event visualization
<Table.Root>
  <Table.Header>
    <Table.Row>
      <Table.ColumnHeader>Event Type</Table.ColumnHeader>
      <Table.ColumnHeader>Resource</Table.ColumnHeader>
      <Table.ColumnHeader>Changes</Table.ColumnHeader>
    </Table.Row>
  </Table.Header>
</Table.Root>
```

## Development Tools

### Code Quality (Enhanced)
```bash
# Backend
ruff check .           # Python linting with scanner modules
ruff format .          # Python formatting
mypy .                 # Type checking including resource models

# Frontend
npm run lint           # ESLint + TypeScript checking with resource types
npm run format         # Prettier formatting
```

### Testing (Enhanced)
```bash
# Backend
pytest                 # Unit and integration tests including scanner tests
pytest --cov          # Coverage reporting
pytest tests/core/yaml_scanner/  # Scanner-specific tests

# Frontend
npm run test           # Playwright E2E tests including resource analytics
```

## Performance Considerations

### Database Optimization (Enhanced)
- **Indexes**: Strategic indexing on resource and event tables for efficient queries
- **Connection Pooling**: SQLAlchemy manages connection lifecycle
- **Query Optimization**: Eager loading for related data, efficient pagination for events
- **Event Partitioning**: Consider time-based partitioning for large event volumes

### Caching Strategy (Enhanced)
- **Redis**: Task queue and potential response caching
- **Database**: Query result caching for expensive operations
- **Frontend**: TanStack Query handles request caching with resource event updates
- **File Content**: Cache GitHub file content to reduce API calls during scanning

### Resource Scanning Performance
- **Batch Processing**: Efficient bulk operations for repository scanning
- **Incremental Updates**: Hash-based change detection to minimize processing
- **Background Tasks**: Non-blocking resource scanning with progress tracking
- **Memory Management**: Efficient memory usage for large repository content

## Monitoring and Observability

### Enhanced Logging
```python
# Structured JSON logging with resource scanning context
import structlog
logger = structlog.get_logger()

logger.info("repository_scan_started", 
            repository_id=repo_id, 
            file_count=file_count)
logger.info("resource_event_generated",
            repository_id=repo_id,
            event_type=event_type,
            resource_kind=resource_kind)
```

### Enhanced Metrics
- **Celery Task Metrics**: Success rates, execution times for scanning tasks
- **API Response Times**: Endpoint performance monitoring including resource endpoints
- **Repository Scan Status**: Track scan success/failure rates and performance
- **Event Volume**: Monitor resource event generation rates and patterns

### Health Checks (Enhanced)
```python
# API health endpoints including scanner health
GET /api/health          # Basic service health
GET /api/health/db       # Database connectivity including resource tables
GET /api/health/redis    # Redis connectivity
GET /api/health/scanner  # Scanner framework health
```

## Deployment Architecture

### Production Considerations (Enhanced)
- **Security**: Environment-based secrets management for GitHub tokens
- **Scalability**: Horizontal scaling with multiple workers for scanning
- **Reliability**: Health checks and graceful shutdown for scanning tasks
- **Monitoring**: Log aggregation and error tracking for scanner operations
- **Performance**: Resource event analytics query optimization

### Infrastructure Requirements (Enhanced)
- **Database**: PostgreSQL 14+ with backup strategy and event retention policies
- **Cache**: Redis for task queue and session storage
- **Compute**: Python 3.11+ runtime with sufficient memory for repository scanning
- **Storage**: Persistent volumes for database data and repository content caching
- **Network**: GitHub API access for content scanning

## Development Constraints

### Technical Constraints (Enhanced)
- **Python Version**: 3.11+ required for modern async features and YAML processing
- **Database**: PostgreSQL required for JSON column support and performance
- **Browser Support**: Modern browsers with ES2020+ support for resource analytics
- **GitHub API**: Rate limiting considerations for content access during scanning
- **Memory Usage**: Large repository scanning requires careful memory management

### Operational Constraints (Enhanced)
- **GitHub API**: Rate limiting (5000/hour authenticated) affects scanning frequency
- **File Processing**: YAML parsing and change detection requires computational resources
- **Network**: External API dependencies require robust error handling
- **Storage**: Event data accumulation requires retention and archival strategies

## Future Technical Considerations

### Scalability Enhancements (Enhanced)
- **Database Sharding**: Partition by time or repository for massive datasets
- **Event Streaming**: Apache Kafka for high-volume event processing
- **Caching Layer**: Redis Cluster for high availability
- **Microservices**: Split scanning into dedicated service
- **Parallel Processing**: Multi-threaded scanning for large repositories

### Integration Expansions (Enhanced)
- **Multiple Git Hosts**: GitLab, Bitbucket support with similar scanning
- **Real-time Updates**: WebSocket connections for live resource events
- **Analytics**: Time-series database for advanced resource trend analysis
- **Kubernetes Integration**: Direct cluster scanning for live resource monitoring
- **CI/CD Integration**: Pipeline integration for repository change detection

### Performance Optimizations (Enhanced)
- **Query Optimization**: Database query performance tuning for resource analytics
- **Streaming Processing**: Stream-based file processing for large repositories
- **Caching Strategies**: Multi-layer caching for resource data and events
- **Incremental Scanning**: Smart file change detection to minimize processing
- **Batch Processing**: Optimize bulk resource operations and event generation

## Current Implementation Status

### Completed Technology Integration ✅
- **FastAPI Backend**: Full API implementation with resource and event endpoints
- **React Frontend**: Complete repository interface with resource analytics
- **PostgreSQL**: Enhanced database schema with resource and event tables
- **Celery Tasks**: Background job processing for repository operations and scanning
- **GitHub API**: Direct integration with HTTPX for repository discovery and content access
- **YAML Scanner**: Complete scanning framework with modular resource scanners
- **TypeScript**: Full type safety between frontend and backend including resource types
- **Chakra UI**: Consistent design system with enhanced analytics components
- **Resource Analytics**: Complete event tracking and visualization system

### Technology Debt and Improvements (Enhanced)
- **Monitoring**: Could enhance observability with structured logging for scanner operations
- **Testing**: Could expand test coverage for edge cases in resource scanning
- **Performance**: Could optimize database queries for very large resource datasets
- **Security**: Could add additional rate limiting and input validation for scanning operations
- **Caching**: Could implement more sophisticated caching for GitHub content and scan results

## Architecture Evolution Summary

The Kubestats technology stack has evolved significantly from a basic repository discovery platform to a comprehensive Kubernetes ecosystem analysis system:

### Key Technology Additions ✅
1. **YAML Processing**: PyYAML integration for Kubernetes resource parsing
2. **Resource Scanning**: Complete modular scanner framework with pluggable scanners
3. **Event Analytics**: Advanced event tracking and visualization with Recharts
4. **Enhanced Database**: Complex schema with resource and event relationships
5. **Performance Optimization**: Strategic indexing and query optimization for analytics
6. **Real-time Updates**: Enhanced TanStack Query integration for live event updates

### Architecture Maturity ✅
- **Modular Design**: Pluggable scanner architecture for extensibility
- **Performance Focus**: Optimized for large-scale resource and event processing
- **Type Safety**: Complete type coverage including resource and event models
- **Analytics Focus**: Advanced visualization and filtering capabilities
- **Production Ready**: Enhanced monitoring, logging, and error handling

The technology stack now supports a sophisticated Kubernetes ecosystem analysis platform with the ability to scale to large numbers of repositories and handle high-volume resource event processing.
