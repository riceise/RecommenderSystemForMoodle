# Repository Guidelines

## Project Structure & Module Organization

This repository has three main areas. `RecommenderSystem.sln` contains the .NET 8 backend projects: `RecommenderSystem.Api` for controllers and app settings, `RecommenderSystem.Core` for entities, DTOs, and interfaces, `RecommenderSystem.Infrastructure` for EF Core persistence, migrations, and services, and `RecommenderSystem.PythonBridge` for Python integration. `PythonService/` contains the Flask recommender service, split into `models/`, `schemas/`, `services/`, `data/`, and `utils/`. `Ui/` is the Vue 3 + Vite frontend; source lives in `Ui/src`.

Do not edit generated `bin/`, `obj/`, `__pycache__/`, or virtual environment files.

## Build, Test, and Development Commands

- `dotnet build RecommenderSystem.sln`: build the backend projects.
- `dotnet run --project RecommenderSystem/RecommenderSystem.Api/RecommenderSystem.Api.csproj`: run the API locally.
- `cd Ui; npm install`: install frontend dependencies.
- `cd Ui; npm run dev`: start the Vite development server.
- `cd Ui; npm run build`: type-check and build the Vue app.ф
- `cd PythonService; pip install -r requirements.txt`: install Python dependencies.
- `cd PythonService; flask --app app run`: run the Python service when Flask environment configuration is available.

## Coding Style & Naming Conventions

Use the existing C# defaults: nullable reference types and implicit usings are enabled. Keep C# types in PascalCase, private fields in camelCase, async methods suffixed with `Async` when applicable, and DTO names ending in `Dto`. Keep controllers in `RecommenderSystem.Api/Controllers` and domain contracts in `Core`.

For Vue, use single-file components in PascalCase, Pinia stores in `Ui/src/stores`, and TypeScript modules with explicit exported types where useful. Python modules should remain snake_case, with Pydantic schemas in `schemas/` and service clients in `services/`.

## Testing Guidelines

No formal test projects or npm test script are currently present. Validate changes with `dotnet build RecommenderSystem.sln`, `npm run build`, and targeted Python smoke checks such as `python test_groq.py` only when credentials are configured. Add future .NET tests under a `*.Tests` project and frontend tests as `*.spec.ts`.

## Commit & Pull Request Guidelines

Recent commits use short, imperative or feature-style summaries such as `AddAdmin`, `Refactor`, and `AddAuth`. Keep commit subjects concise and focused on one change.

Pull requests should include a description, validation steps, related issue or task reference, and screenshots for UI changes. Mention new environment variables, migrations, or external services such as Moodle, Groq, Ollama, PostgreSQL, or search.

## Security & Configuration Tips

Do not commit secrets, API keys, local connection strings, or generated virtual environments. Keep local configuration in untracked environment files or development settings, and document any new required setting in the PR.


# Repository Guidelines

## Project Overview

NeuroTutor is a learning recommender system with three cooperating parts:

- `RecommenderSystem/`: .NET 8 backend API, domain model, EF Core persistence, Moodle sync, and Python bridge.
- `PythonService/`: Flask AI/recommender microservice for recommendations, course analysis, chat, web search discovery, Groq, Ollama, SearXNG, and Postgres access.
- `Ui/`: Vue 3 + Vite frontend with views, layouts, stores, API client, and reusable components.

The .NET API is the main application boundary. It stores Moodle/user/course data in PostgreSQL and calls `PythonService` for AI behavior. The Python service should be treated as an internal dependency, not as the public API surface.

Do not edit generated `bin/`, `obj/`, `__pycache__/`, or virtual environment files.

## Project Structure

- `RecommenderSystem/RecommenderSystem.Api`: ASP.NET Core controllers, auth, app settings, DI setup.
- `RecommenderSystem/RecommenderSystem.Core`: entities, DTOs, interfaces, domain contracts.
- `RecommenderSystem/RecommenderSystem.Infrastructure`: EF Core `AppDbContext`, migrations, Moodle/Python integration services.
- `RecommenderSystem/RecommenderSystem.PythonBridge`: legacy/bridge project for Python recommender calls.
- `PythonService/app.py`: Flask entrypoint and internal AI endpoints.
- `PythonService/services`: Groq, Ollama, SearXNG, Moodle, course analysis, and external course discovery services.
- `PythonService/data/postgres_provider.py`: Python-side DB access for courses, external courses, and recommendation history.
- `Ui/src`: frontend API helpers, components, layouts, stores, and views.

## Core Domain Entities

- `AppUser`: ASP.NET Identity user linked to Moodle by `MoodleUserId`.
- `MoodleStudent`: synced Moodle profile with username, email, full name, and enrolled courses.
- `Course`: internal Moodle course. `ExternalId` is unique; `Topics` is a list of tags/topics.
- `UserCourse`: relation between `MoodleStudent` and `Course`, including course grade, max grade, and last sync time.
- `UserAssignmentGrade`: per-assignment grade under a `UserCourse`.
- `ExternalCourse`: discovered external course from SearXNG/Coursera/edX-like sources. `Url` is unique; `Topics` is stored as JSONB.
- `AiRecommendationHistory`: persisted recommendation snapshot by session/user, linked optionally to internal or external courses.

Key EF relationships are configured in `AppDbContext`: `UserCourse -> MoodleStudent`, `UserCourse -> Course`, and recommendation history links to either `Course` or `ExternalCourse` with `SetNull` on delete.

## Backend API Map

- `api/auth/register`, `api/auth/login`: account creation and JWT login.
- `api/student/courses`: current student course list.
- `api/student/courses/{courseId}`: course details and grades.
- `api/student/statistics`: student statistics.
- `api/student/courses/{courseId}/context`: context for AI/chat.
- `api/student/courses/{courseId}/ai-analysis`: .NET-to-Python course analysis flow.
- `api/recommendations/{username}` and `api/recommendations/recommendations`: recommendation endpoints.
- `api/recommendations/chat`: chat endpoint routed to Python.
- `api/admin/dashboard`, `api/admin/courses`, `api/admin/activity`: admin views.
- `api/admin/sync-all-courses`, `api/admin/sync-users-grades`: Moodle synchronization jobs.

`PythonAiService` is the .NET bridge. It posts to Python endpoints `/recommend`, `/analyze-course`, and `/chat`, then maps the JSON response back into Core DTOs.

## PythonService AI Flow

Python endpoints:

- `GET /health`: basic service health.
- `GET /health/dependencies`: checks Groq key presence, Ollama model availability, SearXNG JSON search, and Postgres.
- `POST /recommend`: hybrid recommendations from internal courses plus cached external courses.
- `POST /analyze-course`: course-specific grade analysis and recommendations.
- `POST /chat`: student chat with recent recommendation context.
- `POST /external-search/discover`: manual external course discovery.

Important behavior:

- Groq is the primary generator for final recommendations, course analysis, and chat.
- SearXNG provides web search results through `SearchService`.
- External course discovery is backgrounded by default so `/analyze-course` and `/recommend` do not block on web search.
- Ollama is available for local LLM tasks, but external discovery does not use it by default. Enable it only with `OLLAMA_EXTERNAL_SEARCH_ENABLED=true`.
- Timeout values are clamped in `utils/config.py`; unsafe `.env` values like `1500` or `2000` seconds should not be allowed to block requests.
- Flask runs with `use_reloader=False` by default to avoid duplicate PythonService processes on port `5001`.

## Search and Local LLM Notes

SearXNG is configured by `PythonService/docker-compose.search.yml` and `PythonService/searxng/settings.yml`.

Required behavior:

- `http://localhost:8080/search?q=health&format=json` must return `200 application/json`.
- `search.formats` must include `json`.
- `SearchService` sends `User-Agent`, `Accept`, `X-Forwarded-For`, and `X-Real-IP` headers.
- If SearXNG fails, PythonService should log the failure and continue with cached/internal recommendations.

Ollama:

- Default URL: `http://localhost:11434`.
- Default model: `qwen3.5:9b`.
- `/api/tags` is enough for health; do not run generation probes in normal dependency checks because local inference can hang.

## Build, Run, and Validation Commands

- `dotnet build RecommenderSystem.sln`: build backend projects.
- `dotnet run --project RecommenderSystem/RecommenderSystem.Api/RecommenderSystem.Api.csproj`: run .NET API.
- `cd PythonService; .\venv\Scripts\python.exe app.py`: run PythonService on port `5001`.
- `cd PythonService; docker compose -f docker-compose.search.yml up -d`: run SearXNG.
- `cd PythonService; .\venv\Scripts\python.exe -m py_compile app.py services\*.py data\*.py utils\*.py`: Python syntax check.
- `curl "http://localhost:8080/search?q=health&format=json"`: verify SearXNG JSON API.
- `Invoke-RestMethod http://localhost:5001/health/dependencies`: verify Python dependencies.
- `cd Ui; npm install`: install frontend dependencies.
- `cd Ui; npm run dev`: start Vite.
- `cd Ui; npm run build`: type-check and build frontend.

## Coding Style

Use the existing C# defaults: nullable reference types and implicit usings are enabled. Keep C# types in PascalCase, private fields in camelCase, async methods suffixed with `Async`, and DTO names ending in `Dto`.

Vue components use PascalCase single-file components. Pinia stores live in `Ui/src/stores`. Python modules use snake_case, Pydantic schemas live in `PythonService/schemas`, and service clients live in `PythonService/services`.

## Testing and Smoke Checks

No formal test projects or npm test script are currently present. Validate changes with targeted smoke checks:

- .NET: `dotnet build RecommenderSystem.sln`.
- Python: `py_compile`, `/health/dependencies`, and a small `/analyze-course` POST.
- Search: SearXNG JSON endpoint must return `200`.
- UI: `npm run build`.

When testing `/analyze-course`, confirm it returns within seconds, not minutes. A long wait usually means a blocking dependency call was reintroduced.

## Configuration and Secrets

Keep secrets out of commits. Important local settings include:

- Python: `GROQ_API_KEY`, `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_NAME`, `PYTHON_SERVICE_PORT`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `WEB_SEARCH_ENABLED`, `SEARXNG_BASE_URL`.
- .NET: `PythonService:Url`, `ConnectionStrings:DefaultConnection`, Moodle URL/token, JWT settings.

Do not commit API keys, Moodle tokens, JWT secrets, local connection strings, virtual environments, or generated build output.

## Commit and PR Guidelines

Recent commits are short and feature-style, such as `AddAdmin`, `Refactor`, and `AddAuth`. Keep commit subjects concise and focused.

Pull requests should include a summary, validation steps, affected services, migration/config notes, and screenshots for visible UI changes. Mention any dependency behavior change involving Groq, Ollama, SearXNG, Moodle, or PostgreSQL.