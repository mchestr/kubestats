You are an expert in **Python, FastAPI, scalable API development, TypeScript, React, Tanstack,** and **Chakra UI**.

### Key Principles

- Write concise, technical responses with accurate examples in both Python and TypeScript.
- Use **functional and declarative programming patterns**; avoid classes unless absolutely necessary.
- Prefer **iteration and modularization** over code duplication.
- Use descriptive variable names with auxiliary verbs (e.g., `is_active`, `has_permission`, `isLoading`, `hasError`).
- Follow proper **naming conventions**:
  - For Python: use lowercase with underscores (e.g., `routers/user_routes.py`).
  - For TypeScript: use lowercase with dashes for directories (e.g., `components/auth-wizard`).

### Project Structure

- **Root Directory**: Contains the main project files and directories.
- **Docker Compose**:
  - `docker-compose.yml`: Main Docker Compose file for orchestrating services.
- **Configuration**:
  - `frontend/.env`: Environment variables for the frontend.
  - `backend/.env`: Environment variables for the backend.
- **Scripts**:
  - `mise.toml`: All project scripts uses `mise` for task management.
- **Environment**:

  - `mise.toml`: `mise` configuration file for managing environment variables and scripts.

- **Frontend**:

  - **Language**: TypeScript
  - **Framework**: React
  - **UI Library**: Chakra UI
  - **State Management**: Tanstack Query
  - **Build Tool**:
    - Vite
  - **API Client**: OpenAPI TypeScript client generated from FastAPI OpenAPI spec
    - Use `mise generate-client` to regenerate the client when the OpenAPI spec changes.
  - **Directory Structure**:
    - `frontend/src/`: Main source code
    - Configuration Files:
      - `vite.config.ts`
      - `tsconfig.json`
      - `openapi-ts.config.ts`
    - **Docker Files**:
      - `Dockerfile`

- **Backend**:
  - **Language**: Python
  - **Framework**: FastAPI
  - **Database**: PostgreSQL
  - **Directory Structure**:
    - `backend/src/`: Main source code
    - `backend/tests/`: Tests
    - `document-processor/`: Document processing utilities
    - Database Configuration:
      - `alembic.ini`
    - **Docker Files**:
      - `Dockerfile`
      - `Dockerfile.dev`

### Code Style and Structure

**Backend (Python/FastAPI)**:

- Use `def` for pure functions and `async def` for asynchronous operations.
- **Type Hints**: Use Python type hints for all function signatures. Prefer Pydantic models for input validation.
- **File Structure**: Follow clear separation with directories for routes, utilities, static content, and models/schemas.
- **RORO Pattern**: Use the "Receive an Object, Return an Object" pattern.
- **Error Handling**:
  - Handle errors at the beginning of functions with early returns.
  - Use guard clauses and avoid deeply nested if statements.
  - Implement proper logging and custom error types.

**Frontend (TypeScript/React)**:

- **TypeScript Usage**: Use TypeScript for all code. Prefer interfaces over types. Avoid enums; use maps instead.
- **Functional Components**: Write all components as functional components with proper TypeScript interfaces.
- **UI and Styling**: Implement responsive design using Chakra UI, adopting a mobile-first approach.
- **Performance**:
  - Minimize `use client`, `useEffect`, and `setState` hooks. Favor server-side rendering where possible.
  - Wrap client components in `Suspense` with fallback for improved performance.

### Testing Conventions

**Critical**: Follow these testing patterns exactly:

**Backend Testing**:

- **NEVER use class-based tests** - Always use individual test functions
- **Function naming**: Use descriptive test function names starting with `test_`
- **Structure**: Follow the pattern in existing test files:
  ```python
  def test_function_name_scenario() -> None:
      """Clear description of what the test validates."""
      # Setup
      # Execute
      # Assert
  ```
