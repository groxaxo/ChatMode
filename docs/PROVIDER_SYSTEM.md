# Provider System Documentation

## Overview

The ChatMode provider system now supports **automatic model discovery and syncing** from any OpenAI-compatible API endpoint. This includes popular providers like:

- **OpenAI** (GPT-4, GPT-3.5, etc.)
- **Ollama** (Local models - Llama, Qwen, etc.)
- **Fireworks AI** (DeepSeek, Llama, etc.)
- **DeepSeek** (DeepSeek-V3, DeepSeek-Coder)
- **xAI (Grok)** (Grok-2, Grok-Beta)
- **Anthropic** (Claude models)
- **LM Studio** (Local GUI for models)
- **vLLM** (Self-hosted model serving)
- **Any OpenAI-compatible API**

## How It Works

### 1. Auto-Discovery on Startup

When the application starts, it automatically:
1. Reads provider configurations from environment variables
2. Detects provider types from URL patterns
3. Creates provider entries in the database
4. Syncs available models from each provider
5. Loads providers into the runtime registry

### 2. Environment Variable Configuration

Simply set your API keys in `.env`:

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Fireworks AI
FIREWORKS_API_KEY=fw-your-key-here

# DeepSeek
DEEPSEEK_API_KEY=sk-your-key-here

# Ollama (local - no key needed)
OLLAMA_BASE_URL=http://localhost:11434
```

The system will automatically detect and sync models from all configured providers!

### 3. API Endpoints

The provider system exposes RESTful endpoints:

#### Provider Management
- `GET /providers` - List all providers
- `POST /providers` - Create a new provider
- `GET /providers/{id}` - Get provider details with models
- `PUT /providers/{id}` - Update provider configuration
- `DELETE /providers/{id}` - Delete a provider

#### Model Syncing
- `POST /providers/{id}/sync` - Sync models from a specific provider
- `POST /providers/sync-all` - Sync models from all enabled providers

#### Testing
- `POST /providers/test` - Test a provider connection without saving

#### Model Management
- `GET /providers/{id}/models` - List models for a provider
- `PUT /providers/{id}/models/{model_id}/enable` - Enable/disable a model
- `GET /providers/available/models` - Get all available models from all providers

## Provider Configuration Format

When creating a provider via API:

```json
{
  "name": "my-openai",
  "display_name": "My OpenAI Account",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "provider_type": "openai",
  "auto_sync_enabled": true
}
```

## Architecture

### Database Models

1. **Provider** - Stores provider configuration
   - `name` - Unique identifier
   - `provider_type` - Type (openai, ollama, etc.)
   - `base_url` - API endpoint
   - `api_key_encrypted` - API key
   - `auto_sync_enabled` - Auto-sync flag
   - `sync_status` - Last sync status
   - `last_sync_at` - Last sync timestamp

2. **ProviderModel** - Stores individual models
   - `model_id` - Model identifier (e.g., "gpt-4o")
   - `display_name` - Human-readable name
   - `supports_tools` - Tool calling capability
   - `supports_vision` - Vision capability
   - `enabled` - Whether model is available for use

### Services

1. **provider_sync.py** - Core sync logic
   - `fetch_models_from_provider()` - Fetches models from APIs
   - `sync_provider_models()` - Syncs models to database
   - `detect_provider_type()` - Auto-detects provider from URL

2. **provider_init.py** - Startup initialization
   - `initialize_providers()` - Sets up providers from env
   - `discover_providers_from_env()` - Discovers from environment
   - `test_provider_connection()` - Tests connections

### Provider Registry

The `providers.py` module maintains a runtime registry:
- `register_provider()` - Register a provider config
- `get_provider_config()` - Get provider configuration
- `load_providers_from_db()` - Load from database on startup
- `build_chat_provider_from_registry()` - Build provider instance

## Sync Process

When syncing models:

1. Query the provider's `/models` endpoint (OpenAI-compatible)
2. For Ollama, use the native `/api/tags` endpoint
3. Parse model IDs and capabilities
4. Auto-detect tool support based on model name patterns
5. Update database (add new, update existing, remove stale)
6. Update provider sync status and timestamp

## Usage Examples

### Adding a Provider via API

```bash
curl -X POST http://localhost:8000/providers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "fireworks",
    "base_url": "https://api.fireworks.ai/inference/v1",
    "api_key": "fw-your-key",
    "auto_sync_enabled": true
  }'
```

### Syncing Models

```bash
# Sync specific provider
curl -X POST http://localhost:8000/providers/{id}/sync \
  -H "Authorization: Bearer YOUR_TOKEN"

# Sync all providers
curl -X POST http://localhost:8000/providers/sync-all \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Testing Connection

```bash
curl -X POST http://localhost:8000/providers/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "base_url": "http://localhost:11434/v1"
  }'
```

## Custom Providers

You can add any OpenAI-compatible provider:

```env
PROVIDER_PERPLEXITY_URL=https://api.perplexity.ai/v1
PROVIDER_PERPLEXITY_KEY=pplx-your-key
```

The system will automatically detect it and sync available models.

## Error Handling

- Connection failures are logged but don't crash the app
- Failed providers show `sync_status: "error"` with error message
- Individual model sync failures don't affect other models
- API returns detailed error messages for troubleshooting

## Security

- API keys are stored encrypted in the database
- Keys are never returned in API responses
- Environment variables are used for initial setup
- Custom headers can be configured per-provider for additional security

## Future Enhancements

Potential improvements:
- Scheduled background syncing (cron-like)
- Model capability detection via API probing
- Provider health monitoring
- Model usage statistics
- Automatic failover between providers
