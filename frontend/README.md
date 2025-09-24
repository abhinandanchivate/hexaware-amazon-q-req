# FHIR Patient Portal Frontend

A React + Redux single-page application that documents and exercises the REST and Kafka APIs for the FHIR Patient Portal platform.

## Features

- Service catalog that mirrors the twelve services defined in the platform specification, including Kafka topic guidance.
- Rich endpoint cards that surface validation rules, Kafka topics, query parameters, and request/response samples.
- Built-in API console that can fire requests against the Django backend using the configured base URL and bearer token.
- Environment drawer for updating the API base URL, bearer token, and Kafka bootstrap servers without rebuilding the app.
- Responsive layout with sidebar navigation optimised for desktop and tablet breakpoints.

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

By default the development server listens on [http://localhost:5173](http://localhost:5173). Update the environment drawer with your backend origin (for example `http://localhost:8000`).

### Production Build

```bash
npm run build
npm run preview
```

The build command outputs a static bundle under `dist/` that can be served by any static file host or reverse-proxy in front of the Django backend.

## Project Structure

```
frontend/
├── index.html              # Vite entry point
├── package.json            # npm dependencies
├── src/
│   ├── App.jsx             # Application shell
│   ├── styles.css          # Global styles
│   ├── app/store.js        # Redux store
│   ├── components/         # UI components (sidebar, headers, endpoint cards)
│   └── features/           # Redux slices and feature-specific components
└── vite.config.js          # Vite configuration
```

## API Console

- **Send Request** executes the sample payload against the configured backend. Update headers or JSON as needed before sending.
- **Reset Sample** restores the canonical request body from the specification.
- **Show Response** toggles between example payloads and live responses from the backend.

> **Note:** If you do not have the backend running locally the Send Request action will surface a network error inside the response panel. The rest of the documentation remains fully interactive.

## Kafka Documentation

The Kafka section consolidates topic architecture, schemas, retention settings, dead-letter queues, consumer patterns, monitoring, and security expectations from the specification. Each card is copy-ready to feed into Confluence, architecture diagrams, or observability dashboards.

## Browser Compatibility

The application targets evergreen browsers (Chrome, Edge, Firefox, Safari). No TypeScript or CSS frameworks are required.
