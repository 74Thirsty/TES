# Task & Event Scheduler (TES)

TES is a feature-rich productivity API for managing tasks and events, tracking focus, and surfacing actionable insights. It relies only on the Node.js standard library so it can run anywhere without installing third-party packages.

## Features

- **Robust task management** – create, update, filter, and complete tasks with priorities, due dates, estimates, and tags.
- **Powerful event planning** – capture meetings and appointments with locations, all-day support, tags, and smart validation.
- **Insightful analytics** – overview and focus endpoints summarise workload, overdue items, and the next best action.
- **Zero dependencies** – no external packages required. Data is persisted to JSON (or in-memory for testing).
- **Ready for automation** – clean REST surface, CORS enabled, and JSON-based error responses.

## Getting started

1. **Install Node.js 18+** (already available in most environments).
2. **Clone and run**

   ```bash
   npm install  # optional, provided for completeness – no dependencies are downloaded
   npm run dev
   ```

   The server listens on `http://localhost:4000` by default.

3. **Configure environment variables (optional)**

   Copy `.env.example` to `.env` and adjust values if needed.

   ```bash
   cp .env.example .env
   ```

   - `PORT` controls the HTTP port.
   - `TES_DB_FILE` controls the persistence file. Set to `:memory:` for ephemeral storage.

4. **Run the test suite**

   ```bash
   npm test
   ```

   Tests are powered by the built-in `node:test` runner and hit the live HTTP server.

## REST API quick reference

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `GET` | `/api/tasks` | List tasks with pagination, filtering, and search |
| `POST` | `/api/tasks` | Create a task |
| `GET` | `/api/tasks/:id` | Retrieve a task |
| `PATCH` | `/api/tasks/:id` | Update fields on a task |
| `POST` | `/api/tasks/:id/complete` | Mark a task as completed |
| `DELETE` | `/api/tasks/:id` | Delete a task |
| `GET` | `/api/events` | List events with optional range filtering |
| `POST` | `/api/events` | Create an event |
| `GET` | `/api/events/:id` | Retrieve an event |
| `PATCH` | `/api/events/:id` | Update event details |
| `DELETE` | `/api/events/:id` | Remove an event |
| `GET` | `/api/statistics/overview` | Snapshot of workload and upcoming commitments |
| `GET` | `/api/statistics/focus` | Focus recommendations for what to do next |
| `GET` | `/api/health` | Lightweight health check |

### Task payload

```json
{
  "title": "Ship TES release",
  "description": "Write docs and run launch checklist",
  "status": "pending",
  "priority": 4,
  "dueDate": "2024-07-10T09:00:00.000Z",
  "estimatedMinutes": 120,
  "tags": ["product", "release"]
}
```

### Event payload

```json
{
  "name": "Weekly product sync",
  "description": "Discuss roadmap and blockers",
  "location": "Zoom",
  "startTime": "2024-07-02T15:00:00.000Z",
  "endTime": "2024-07-02T16:00:00.000Z",
  "allDay": false,
  "tags": ["team", "meeting"]
}
```

## Project structure

```
TES/
├── data/              # JSON persistence (or use :memory: for ephemeral mode)
├── src/
│   ├── services/      # Business logic for tasks, events, and statistics
│   ├── app.js         # HTTP server factory
│   ├── router.js      # Request routing and validation glue
│   ├── storage.js     # Lightweight persistence helpers
│   ├── validators.js  # Input validation utilities
│   ├── http.js        # JSON helpers and CORS handling
│   └── server.js      # CLI entrypoint
├── tests/             # node:test integration tests
├── .env.example       # Environment variable template
├── package.json
└── README.md
```

## Development tips

- Use the `TES_DB_FILE=:memory:` environment variable to run against an ephemeral database during tests or experimentation.
- Because the API has no runtime dependencies you can bundle or deploy it as a single file.
- All responses are JSON and include helpful error messages (`error` and optional `details` fields).

## License

ISC © gadgetsaavy
