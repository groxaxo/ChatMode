# ChatMode React Frontend

Modern React UI for ChatMode with agent management, live monitoring, and session control.

## Quick Start

```bash
npm install
npm run dev
```

Backend must be running on port 8000.

## Build

```bash
npm run build
npm run preview
```

## API Notes

The app uses the existing ChatMode API:
- Auth: `/api/v1/auth/*`
- Sessions: `/api/v1/conversations/*`
- Agents: `/api/v1/agents/*`
- Filter: `/api/v1/filter/*`

## Customization

Update styles in [src/index.css](src/index.css) and theme tokens in [tailwind.config.js](tailwind.config.js).
