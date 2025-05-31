# System Patterns: Kubestats

## Current Architecture Overview

### System Design Philosophy
Kubestats follows a **microservice-inspired monolithic architecture** with clear separation of concerns between data discovery, processing, and presentation layers. The system is designed for scalability while maintaining development simplicity.

## Implemented System Patterns

### 1. Repository-Centric Data Model ✅ **IMPLEMENTED**

#### Pattern Description
All data in Kubestats revolves around Git repositories as the primary entity, with associated metrics and resources tracked over time.

#### Implementation
```python
# Core entity relationships (Implemented)
Repository (1) -> (Many) RepositoryMetrics     # Time-series metrics snapshots
Repository (1) -> (Many) KubernetesResource    # Discovered K8s resources
```

#### Benefits
- **Temporal Analytics**: Track repository evolution over time
- **Resource Correlation**: Link Kubernetes resources to their source repositories
- **Sync Management**: Track synchronization status per repository
- **Scalable Queries**: Efficient data retrieval by repository or time range

### 2. Task-Based Background Processing ✅ **IMPLEMENTED**

#### Pattern Description
Long-running operations (discovery, sync, scanning) are handled asynchronously via Celery tasks to maintain responsive user experience.

#### Current Implementation
```python
# Implemented task patterns
@shared_task(bind=True, max_retries=3)
def discover_repositories(self):
    # GitHub API repository discovery
    # Database persistence with deduplication
    # Error handling with exponential backoff

@shared_task(bind=True, max_retries=3) 
def sync_repository(self, repository_id: str, create_metrics: bool = False):
    # Individual repository synchronization
    # Metrics snapshot creation
    # Status tracking and error reporting

@shared_task(bind=True, max_retries=3)
def sync_all_repositories(self, create_metrics: bool = False):
    # Bulk repository synchronization
    # Parallel processing coordination
    # Progress tracking
```

#### Scheduling Configuration (Ready for Activation)
```python
# Celery Beat schedule (Framework ready)
beat_schedule = {
    "discover-repositories": {
        "task": "kubestats.tasks.discover_repositories.run",
        "schedule": 300.0,  # 5 minutes
    },
    "sync-repositories": {
        "task": "kubestats.tasks.sync_repositories.sync_all_repositories", 
        "schedule": 900.0,  # 15 minutes
    },
}
```

### 3. API-First Design ✅ **IMPLEMENTED**

#### Pattern Description
All functionality is exposed through RESTful APIs with auto-generated documentation, enabling both web interface and programmatic access.

#### Implementation Details
```python
# Complete repository API (Implemented)
GET    /api/v1/repositories/                    # List with filtering and pagination
GET    /api/v1/repositories/stats               # Ecosystem statistics
GET    /api/v1/repositories/search              # Search functionality
GET    /api/v1/repositories/{id}                # Repository details with latest metrics
GET    /api/v1/repositories/{id}/metrics        # Historical metrics time-series
POST   /api/v1/repositories/discover            # Manual discovery trigger
POST   /api/v1/repositories/{id}/sync           # Single repository sync
POST   /api/v1/repositories/sync-all            # Bulk sync operation

# Auto-generated OpenAPI specification available at /docs
```

#### Benefits
- **Type Safety**: Pydantic models ensure request/response validation
- **Documentation**: Interactive API docs with examples
- **Client Generation**: TypeScript client auto-generated from OpenAPI spec
- **Future Extensibility**: Easy to add new endpoints and functionality

### 4. Component-Based Frontend Architecture ✅ **IMPLEMENTED**

#### Pattern Description
React components organized by feature with consistent patterns for data fetching, state management, and UI interactions.

#### Repository Management Components (Complete)
```typescript
// Implemented component hierarchy
frontend/src/components/Repositories/
├── Repositories.tsx           // ✅ Main repository list with filtering
├── RepositoryDetail.tsx       // ✅ Individual repository view
├── MetricsCards.tsx          // ✅ Current metrics display cards
├── MetricsChart.tsx          // ✅ Historical metrics visualization
├── RepositoryInfo.tsx        // ✅ Repository information display

// Route structure (Complete)
frontend/src/routes/_layout/
├── repositories.tsx          // ✅ Repository layout route
├── repositories/            
│   ├── index.tsx            // ✅ Repository list page
│   └── $repositoryId.tsx    // ✅ Repository detail page
```

#### State Management Patterns (Implemented)
```typescript
// Server state management with TanStack Query
const { data: repositories, isLoading, isError } = useQuery({
  queryKey: ["repositories"],
  queryFn: () => RepositoriesService.repositoriesReadRepositories({}),
})

// Local state management with React hooks
const [filters, setFilters] = useState<RepositoryFilters>({
  search: "",
  language: "",
  syncStatus: "",
})

// Optimistic updates and cache invalidation
const queryClient = useQueryClient()
await queryClient.invalidateQueries({ queryKey: ["repositories"] })
```

### 5. Sync Status Management ✅ **IMPLEMENTED**

#### Pattern Description
Comprehensive tracking of repository synchronization states with visual indicators and manual trigger capabilities.

#### Implementation
```typescript
// Sync status tracking (Implemented)
type SyncStatus = "pending" | "syncing" | "success" | "error"

// Visual status indicators
const getSyncStatusBadge = (repo: RepositoryPublic) => {
  switch (repo.sync_status) {
    case "success": return <Badge colorPalette="green">✓ Synced</Badge>
    case "pending": return <Badge colorPalette="yellow">⏱ Pending</Badge>
    case "syncing": return <Badge colorPalette="blue">↻ Syncing</Badge>
    case "error": return <Badge colorPalette="red">✗ Error</Badge>
  }
}

// Manual sync triggers (Individual and bulk)
<SyncButton onSync={(createMetrics) => handleTriggerSync(repo.id, createMetrics)} />
<SyncButton onSync={(createMetrics) => handleTriggerAllSync(createMetrics)}>Sync All</SyncButton>
```

### 6. GitHub API Integration Strategy ✅ **IMPLEMENTED**

#### Pattern Description
Direct GitHub API integration using HTTPX with proper authentication, rate limiting, and error handling.

#### Implementation Details
```python
# Direct API client implementation (Complete)
class GitHubClient:
    def __init__(self, token: str):
        self.client = httpx.Client(
            headers={"Authorization": f"token {token}"},
            timeout=30.0
        )
    
    def search_repositories(self, query: str) -> Dict[str, Any]:
        # Direct GitHub API calls with authentication
        # Handles rate limiting (5000/hour authenticated)
        # Returns paginated results (up to 100 per page)
    
    def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        # Fetch detailed repository metadata
        # Include metrics, topics, license information
    
    def get_repository_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        # Fetch repository file contents for scanning
        # Support recursive directory traversal
```

#### Benefits
- **Simplified Architecture**: No external MCP dependencies
- **Better Control**: Direct management of API calls and error handling
- **Performance**: Efficient synchronous API calls with connection pooling
- **Rate Limiting**: Proper handling of GitHub's API limits

### 7. Time-Series Metrics Pattern ✅ **IMPLEMENTED**

#### Pattern Description
Repository metrics are captured as periodic snapshots, enabling historical trend analysis and change detection.

#### Database Schema (Implemented)
```sql
-- Metrics snapshots table
repositorymetrics (
  id UUID PRIMARY KEY,
  repository_id UUID REFERENCES repository(id),
  stars_count INTEGER,
  forks_count INTEGER, 
  watchers_count INTEGER,
  open_issues_count INTEGER,
  size INTEGER,
  updated_at TIMESTAMP,
  pushed_at TIMESTAMP,
  recorded_at TIMESTAMP DEFAULT NOW()
)

-- Efficient querying with indexes
CREATE INDEX idx_repositorymetrics_repo_recorded 
ON repositorymetrics(repository_id, recorded_at DESC);
```

#### Visualization Implementation (Complete)
```typescript
// Historical metrics chart component
function MetricsChart({ metrics }: MetricsChartProps) {
  // Time-series visualization using Recharts
  // Multiple metrics on same chart with different scales
  // Interactive tooltips showing exact values
  // Responsive design for different screen sizes
}
```

### 8. Search and Filtering Patterns ✅ **IMPLEMENTED**

#### Pattern Description
Multi-criteria filtering with instant search, language filtering, and sync status filtering across large repository datasets.

#### Frontend Implementation (Complete)
```typescript
// Advanced filtering component (Implemented)
interface RepositoryFilters {
  search: string         // Name and full_name search
  language: string       // Programming language filter
  syncStatus: string     // Sync status filter
}

// Filter application with memoized results
const { filteredRepositories, paginatedRepositories, totalFilteredItems } = useMemo(() => {
  const allRepos = repositoryData?.data || []
  
  // Apply search filter (name and full_name)
  const filtered = allRepos.filter((repo) => {
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase()
      const matchesName = repo.name.toLowerCase().includes(searchTerm)
      const matchesFullName = repo.full_name.toLowerCase().includes(searchTerm)
      if (!matchesName && !matchesFullName) return false
    }
    
    // Apply language and sync status filters
    if (filters.language && repo.language !== filters.language) return false
    if (filters.syncStatus && (repo.sync_status || "pending") !== filters.syncStatus) return false
    
    return true
  })
  
  // Apply pagination
  const startIndex = (currentPage - 1) * itemsPerPage
  const paginated = filtered.slice(startIndex, startIndex + itemsPerPage)
  
  return { filteredRepositories: filtered, paginatedRepositories: paginated, totalFilteredItems: filtered.length }
}, [repositoryData?.data, filters, currentPage, itemsPerPage])
```

### 9. Error Handling and Resilience Patterns ✅ **IMPLEMENTED**

#### Pattern Description
Comprehensive error handling with retry logic, user feedback, and graceful degradation.

#### Backend Error Handling (Implemented)
```python
# Task retry patterns with exponential backoff
@shared_task(bind=True, max_retries=3)
def sync_repository(self, repository_id: str):
    try:
        # Repository sync logic
        pass
    except Exception as exc:
        # Log error details
        logger.error("Repository sync failed", repository_id=repository_id, error=str(exc))
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# API error responses
class RepositoryNotFound(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Repository not found")
```

#### Frontend Error Handling (Implemented)
```typescript
// Query error states with user feedback
const { data, isLoading, isError, error } = useQuery({
  queryKey: ["repository", repositoryId],
  queryFn: () => RepositoriesService.repositoriesReadRepository({
    path: { repository_id: repositoryId }
  }),
  retry: 3,           // Automatic retry on failure
  retryDelay: 1000,   // Progressive retry delays
})

// User-friendly error displays
if (isError) {
  return (
    <Card.Root>
      <Card.Body textAlign="center" py={12}>
        <Text color="red.500" fontSize="lg" fontWeight="medium">
          Repository not found
        </Text>
        <Text color="fg.muted" mt={2}>
          The repository you're looking for doesn't exist or you don't have access to it.
        </Text>
        <Button mt={4} asChild>
          <RouterLink to="/repositories">Back to Repositories</RouterLink>
        </Button>
      </Card.Body>
    </Card.Root>
  )
}
```

### 10. Responsive Data Loading Patterns ✅ **IMPLEMENTED**

#### Pattern Description
Progressive loading with skeleton screens, loading states, and efficient pagination to handle large datasets.

#### Implementation (Complete)
```typescript
// Progressive loading with skeleton screens
if (isLoading) {
  return (
    <Container maxW="full">
      <Stack gap={6}>
        <Skeleton height="60px" />
        <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4}>
          <Skeleton height="100px" />
          <Skeleton height="100px" />
          <Skeleton height="100px" />
          <Skeleton height="100px" />
        </Grid>
        <Skeleton height="400px" />
      </Stack>
    </Container>
  )
}

// Efficient pagination implementation
const handlePageChange = (page: number) => {
  setCurrentPage(page)
}

const handleItemsPerPageChange = (newItemsPerPage: number) => {
  setItemsPerPage(newItemsPerPage)
  setCurrentPage(1) // Reset to first page when changing page size
}

// Pagination component with configurable page sizes
<Pagination
  currentPage={currentPage}
  totalItems={totalFilteredItems}
  itemsPerPage={itemsPerPage}
  onPageChange={handlePageChange}
  onItemsPerPageChange={handleItemsPerPageChange}
/>
```

## Architectural Decisions and Tradeoffs

### 1. Monolithic vs Microservices ✅ **DECISION MADE**
**Decision**: Monolithic architecture with clear internal boundaries
**Reasoning**: 
- Simpler deployment and development
- Easier transaction management across repositories and metrics
- Can evolve to microservices later if needed
**Implementation**: Single FastAPI application with feature-based module organization

### 2. Synchronous vs Asynchronous GitHub API Access ✅ **DECISION MADE**
**Decision**: Synchronous HTTPX client in background tasks
**Reasoning**:
- Simpler error handling and retry logic
- Better control over rate limiting
- Background task processing eliminates blocking concerns
**Implementation**: Direct HTTPX client with connection pooling and timeout handling

### 3. Real-time vs Batch Processing ✅ **DECISION MADE**
**Decision**: Periodic batch processing with manual triggers
**Reasoning**:
- More reliable than webhook-based real-time updates
- Better GitHub API rate limiting management
- Simpler error recovery and monitoring
**Implementation**: Celery Beat scheduler with 5-minute discovery and 15-minute sync intervals

### 4. Component State Management ✅ **DECISION MADE**
**Decision**: TanStack Query for server state, React hooks for local state
**Reasoning**:
- Excellent caching and background synchronization
- Built-in loading and error states
- Optimistic updates and cache invalidation
**Implementation**: Query client with strategic cache invalidation after mutations

### 5. Database Schema Design ✅ **DECISION MADE**
**Decision**: Time-series metrics with snapshot approach
**Reasoning**:
- Enables historical trend analysis
- Simple to query and aggregate
- Supports metrics evolution over time
**Implementation**: Separate RepositoryMetrics table with foreign key relationship

## Performance Patterns

### 1. Database Query Optimization ✅ **IMPLEMENTED**
```sql
-- Strategic indexing for common queries
CREATE INDEX idx_repository_github_id ON repository(github_id);
CREATE INDEX idx_repository_sync_status ON repository(sync_status);
CREATE INDEX idx_repositorymetrics_repo_recorded ON repositorymetrics(repository_id, recorded_at DESC);

-- Efficient pagination queries
SELECT * FROM repository 
ORDER BY discovered_at DESC 
LIMIT 25 OFFSET 0;
```

### 2. Frontend Performance Patterns ✅ **IMPLEMENTED**
```typescript
// Memoized expensive computations
const { filteredRepositories, paginatedRepositories, totalFilteredItems } = useMemo(() => {
  // Filtering and pagination logic
}, [repositoryData?.data, filters, currentPage, itemsPerPage])

// Efficient re-renders with proper dependency arrays
useEffect(() => {
  // Effect logic with specific dependencies
}, [repositoryId])

// Component-level code splitting (ready for implementation)
const RepositoryDetail = lazy(() => import('./RepositoryDetail'))
```

### 3. Caching Strategies ✅ **IMPLEMENTED**
```typescript
// TanStack Query automatic caching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,    // 5 minutes
      cacheTime: 10 * 60 * 1000,   // 10 minutes
      retry: 3,
    },
  },
})

// Strategic cache invalidation
await queryClient.invalidateQueries({ queryKey: ["repositories"] })
await queryClient.invalidateQueries({ queryKey: ["repository", repositoryId] })
```

## Security Patterns

### 1. Authentication and Authorization ✅ **IMPLEMENTED**
```python
# JWT token-based authentication
@app.post("/api/v1/login/access-token")
def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authenticate user and return JWT token
    pass

# Protected route pattern
@app.get("/api/v1/repositories/", dependencies=[Depends(get_current_active_user)])
def read_repositories():
    # Only accessible with valid JWT token
    pass
```

### 2. Input Validation ✅ **IMPLEMENTED**
```python
# Pydantic model validation for all inputs
class RepositoryCreate(RepositoryBase):
    github_id: int = Field(..., gt=0)  # Must be positive integer
    name: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)

# URL parameter validation
@app.get("/api/v1/repositories/{repository_id}")
def read_repository(repository_id: uuid.UUID = Path(...)):
    # UUID validation automatically handled
    pass
```

### 3. Rate Limiting Considerations ✅ **IMPLEMENTED**
```python
# GitHub API rate limiting awareness
def search_repositories(query: str) -> Dict[str, Any]:
    response = client.get(
        "https://api.github.com/search/repositories",
        params={"q": query, "per_page": 100},
        headers={"Authorization": f"token {github_token}"}
    )
    
    # Check rate limit headers
    remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
    if remaining < 100:
        logger.warning("GitHub API rate limit approaching", remaining=remaining)
    
    return response.json()
```

## Monitoring and Observability Patterns

### 1. Structured Logging ✅ **READY FOR IMPLEMENTATION**
```python
# Structured logging with contextual information
import structlog
logger = structlog.get_logger()

@shared_task(bind=True)
def sync_repository(self, repository_id: str):
    logger.info("repository_sync_started", 
                repository_id=repository_id, 
                task_id=self.request.id)
    try:
        # Sync logic
        logger.info("repository_sync_completed", 
                   repository_id=repository_id,
                   duration=execution_time)
    except Exception as exc:
        logger.error("repository_sync_failed",
                    repository_id=repository_id,
                    error=str(exc),
                    traceback=traceback.format_exc())
```

### 2. Health Check Patterns ✅ **READY FOR IMPLEMENTATION**
```python
# Health check endpoints for monitoring
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/health/db")
def health_check_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "database"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {exc}")
```

## Future Pattern Considerations

### 1. Scalability Patterns (Future)
- **Horizontal Scaling**: Multiple Celery workers for parallel task processing
- **Database Sharding**: Partition repositories by organization or time
- **Caching Layer**: Redis cluster for high-availability caching
- **Load Balancing**: Multiple backend instances behind load balancer

### 2. Integration Patterns (Future)
- **Event-Driven Architecture**: WebSocket updates for real-time repository status
- **API Gateway**: Rate limiting and request routing for external API access
- **Message Queue**: RabbitMQ or Apache Kafka for high-throughput task processing
- **External Integration**: GitLab, Bitbucket, and other git hosting platforms

### 3. Analytics Patterns (Future)
- **Time-Series Database**: InfluxDB or TimescaleDB for advanced metrics analysis
- **Data Pipeline**: ETL processes for repository trend analysis and predictions
- **Real-time Analytics**: Stream processing for live repository activity monitoring
- **Comparative Analysis**: Repository ranking and ecosystem health metrics

## Pattern Evolution Summary

The Kubestats system has evolved from a basic repository listing to a comprehensive repository management platform with the following key patterns successfully implemented:

1. ✅ **Repository-Centric Data Model** - Complete with time-series metrics
2. ✅ **Task-Based Background Processing** - Celery framework with retry logic
3. ✅ **API-First Design** - Complete RESTful API with OpenAPI documentation
4. ✅ **Component-Based Frontend** - Full React component architecture
5. ✅ **Sync Status Management** - Comprehensive status tracking and manual triggers
6. ✅ **GitHub API Integration** - Direct HTTPX client implementation
7. ✅ **Time-Series Metrics** - Historical data capture and visualization
8. ✅ **Search and Filtering** - Multi-criteria filtering with pagination
9. ✅ **Error Handling and Resilience** - Retry logic and user feedback
10. ✅ **Responsive Data Loading** - Progressive loading with skeleton screens

These patterns provide a solid foundation for the current repository management functionality and can be extended to support future enhancements in discovery automation, advanced analytics, and ecosystem insights.
