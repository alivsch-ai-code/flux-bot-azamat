# System Block Diagram (Simulink-style)

Dieses Blockdiagramm zeigt den End-to-End-Datenfluss des Bots mit Telegram, WebApp, Flask-API, Service-Layer, Replicate und Neon.

```mermaid
flowchart LR
  U[User] --> TG[Telegram Client]
  U --> WA[Telegram WebApp]

  TG --> BOT[aiogram Bot Layer]
  WA --> API[Flask API Layer]

  BOT --> H[Telegram Handlers]
  API --> HHTTP[HTTP Routes]

  H --> GS[GenerationService]
  HHTTP --> GS

  GS --> UAI[UnifiedAIClient]
  UAI --> RS[Replicate SDK/API]

  RS --> UAI
  UAI --> GS
  GS --> H
  GS --> HHTTP

  H --> DB[(Neon PostgreSQL)]
  HHTTP --> DB
  GS --> DB

  DB --> H
  DB --> HHTTP
  DB --> GS

  subgraph Replicate Path
    UAI --> INP[Schema Adapter\ninput_schema mapping]
    INP --> RS
    RS --> OUT[Output Normalization\n+ Delivery Routing]
    OUT --> UAI
  end
```

## Kurzbeschreibung

- **Telegram/WebApp** sind zwei Frontends für denselben Kern.
- **GenerationService** ist die zentrale Anwendungslogik (Kosten, Prompt-Flow, Weiterleitung).
- **UnifiedAIClient** kapselt Provider-Details (v. a. Replicate).
- **Neon DB** hält Nutzer, Modelle (`ai_models` inkl. Input/Output-Schema), Einstellungen und Betriebsdaten.

