# Smart Agriculture Real AI Agronomist Chat Architecture & Guide (Phase E)

This document details the architecture, provider abstraction, local Ollama integration, context builder, and security protocols for the **Harvesta Real AI Agronomist Chat (Phase E)**.

---

## 1. System Architecture Overview

The Harvesta AI Chat system provides contextualized precision agricultural intelligence directly to farmers using a modular, provider-agnostic backend.

```
┌──────────────────────────────────────────────────────────┐
│              Harvesta React Frontend                     │
│         (ChatWidget.jsx & API Service)                   │
└────────────────────────────┬─────────────────────────────┘
                             │ POST /api/chat/conversations
                             │ POST /api/chat/conversations/{id}/messages
                             ▼
┌──────────────────────────────────────────────────────────┐
│              FastAPI Backend Router                      │
│             (backend/app/routes/chat.py)                 │
└────────────────────────────┬─────────────────────────────┘
                             │
     ┌───────────────────────┼────────────────────────┐
     ▼                       ▼                        ▼
┌──────────────┐    ┌─────────────────┐    ┌────────────────────┐
│ User Auth &  │    │ Precision Farm  │    │ Conversation DB    │
│  Ownership   │    │ Context Builder │    │  (PostgreSQL /     │
│ Verification │    │                 │    │     SQLite)        │
└──────────────┘    └────────┬────────┘    └────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│              LLM Provider Abstraction Layer              │
│            (backend/app/services/llm/)                   │
├──────────────────────────────────────────────────────────┤
│  • Local Mode: OllamaProvider (http://127.0.0.1:11434)   │
│  • Model: qwen2.5-coder:7b                               │
│  • Future Mode: Cloud API / Self-Hosted Serverless LLM   │
└──────────────────────────────────────────────────────────┘
```

---

## 2. AI Provider Abstraction (`backend/app/services/llm/`)

The backend interface is decoupled from specific model providers via the `LLMProvider` abstract base class:

- **`LLMProvider` (`base.py`)**: Abstract base class defining `generate_chat_response(messages, temperature, max_tokens)`.
- **`OllamaProvider` (`ollama_provider.py`)**: Asynchronous HTTP client communicating directly with the local Ollama daemon (`/api/chat`).
- **`get_llm_provider()` (`__init__.py`)**: Factory function resolving active provider based on environment configuration (`AI_PROVIDER`).

---

## 3. Environment Configuration

| Variable | Default Value | Description |
|---|---|---|
| `AI_PROVIDER` | `ollama` | Provider identifier (`ollama`, future `hosted_api`) |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | HTTP endpoint of local Ollama server |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Name of Ollama model loaded for inference |
| `CHAT_MODEL_TIMEOUT_SECONDS` | `6` | Interactive deadline before safe built-in guidance is returned |

Phone voice setup and HTTPS requirements are in
[`PHONE-VOICE-CHAT.md`](PHONE-VOICE-CHAT.md).

> **Note**: Local Ollama runs completely quota-free without external API credits or cloud charges.

---

## 4. Precision Farmer Context Builder

Each prompt dynamically gathers bounded, non-sensitive context belonging exclusively to the authenticated user:
1. **Farmer Identity**: User name.
2. **Farms**: Registered farm names, acreage/hectares, and location.
3. **Crops**: Active crops and current growth stages.
4. **Latest Field Analysis**: Measured soil moisture, temperature, humidity, rainfall, and irrigation recommendation status.
5. **Recent Weather Snapshot**: Microclimate conditions, ambient temperature, precipitation.
6. **Latest Disease Vision Scan**: Identified crop, disease class, confidence %, and agronomic guidelines.
7. **Active High-Priority Alerts**: Unread disease, weather, or irrigation advisories.

### Security & Privacy Protections:
- **Zero Secret Exposure**: Passwords, hashes, JWT tokens, SMTP credentials, and raw audit metadata are strictly excluded from prompts.
- **Strict User Isolation**: Context contains only records belonging to `current_user.id`.
- **Telemetry Sanitization**: `ai_chat_message` activity events record metadata (`conversation_id`, `model`, `msg_len`) without logging the raw conversational text.

---

## 5. Agronomist System Prompt Rules

The AI Agronomist operates under conservative precision agriculture principles:
- **Domain Focus**: Agronomy, crop physiology, irrigation management, soil moisture, and pest/disease cultural prevention.
- **Factual Grounding**: Distinguishes measured telemetry from general recommendations.
- **No Hallucination**: Never fabricates unmeasured sensors (e.g. NPK, electrical conductivity, satellite NDVI).
- **Non-Prescriptive Guidance**: Disease vision outputs are treated as AI screening, not medical/botanical prescriptions. For severe infestations, professional extension consultation is recommended.

---

## 6. REST API Reference

### 1. `POST /api/chat/conversations`
Creates a new conversation session.
- **Body**: `{"title": "Optional Title", "farm_id": 1}`
- **Response (201 Created)**: `{"id": 1, "user_id": 42, "title": "...", "created_at": "..."}`

### 2. `GET /api/chat/conversations`
Lists authenticated user's conversations (paginated, newest first).

### 3. `GET /api/chat/conversations/{id}`
Retrieves conversation details and ordered message thread.

### 4. `DELETE /api/chat/conversations/{id}`
Deletes conversation and cascade-deletes all child messages.

### 5. `POST /api/chat/conversations/{id}/messages`
Sends user message, builds agricultural context, queries provider, and returns assistant response.
- **Body**: `{"message": "How often should I water my tomatoes?"}`
- **Response (200 OK)**:
```json
{
  "user_message": {
    "id": 10,
    "conversation_id": 1,
    "role": "user",
    "content": "How often should I water my tomatoes?",
    "created_at": "2026-08-30T14:30:00Z"
  },
  "assistant_message": {
    "id": 11,
    "conversation_id": 1,
    "role": "assistant",
    "content": "For your registered Tomato crop (currently Flowering stage)...",
    "model_name": "qwen2.5-coder:7b",
    "created_at": "2026-08-30T14:30:04Z"
  },
  "conversation": {
    "id": 1,
    "title": "How often should I water my tomatoes?",
    "updated_at": "2026-08-30T14:30:04Z"
  }
}
```

---

## 7. Failure & Graceful Degradation Handling

If the local Ollama daemon is offline or the model is loading:
- The backend returns HTTP `503 Service Unavailable` with a user-friendly explanation:
  `"Local AI assistant is currently unreachable at http://127.0.0.1:11434. Please ensure Ollama is running with model 'qwen2.5-coder:7b'."`
- **No fake assistant messages** are written to the database.
- The frontend displays an inline notification banner with instructions without crashing the UI.

---

## 8. Production Limitations & Future Provider Migration

- **Local Machine Dependency**: Local Ollama execution runs on the developer machine CPU/GPU. In public production deployment, a hosted model (e.g. self-hosted vLLM instance or secure hosted LLM endpoint) should be configured in `AI_PROVIDER`.
- **Frontend Independence**: The frontend calls only the backend `/api/chat/*` routes and is completely agnostic to whether the backend is powered by Ollama or a cloud provider.
