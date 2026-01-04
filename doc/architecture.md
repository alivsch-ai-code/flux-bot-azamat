graph TD
%% --- Externe Welt ---
User[👤 Nutzer / Handy] -- "Klickt Bild generieren & tippt Prompt" --> TG_Server[Telegram Server]
TG_Server -- "Sendet Update Webhook/Polling" --> BotInstance[🤖 Deine Bot Instanz main.py]

    %% --- Layer 1: Presentation (Die Rezeption) ---
    subgraph L1 ["1. Presentation Layer (src/presentation)"]
        Bot[bot.py TeleBot]
        Handlers[Handlers gen_handler.py, menu_handler.py]
    end

    BotInstance --> Bot
    Bot -- "Leitet Nachricht weiter" --> Handlers

    %% --- Layer 2: Application (Das Gehirn) ---
    subgraph L2 ["2. Application Layer (src/application)"]
        GenService[GenerationService Business Logik]
    end

    Handlers -- "Ruft auf: service.process_request()" --> GenService

    %% --- Layer 3: Domain (Die Gesetze & Verträge) ---
    subgraph L3 ["3. Domain Layer (src/domain)"]
        Interfaces[Interfaces contracts.py]
        Entities[Entities User, AIModel]

        note_interfaces["📝 Verträge: UserRepository, AIProvider"]
        Interfaces --- note_interfaces
    end

    GenService -- "Nutzt Datenstruktur" --> Entities
    GenService -- "Kennt NUR die Verträge" --> Interfaces

    %% --- Layer 4: Infrastructure (Die Maschinen) ---
    subgraph L4 ["4. Infrastructure Layer (src/infrastructure)"]
        InMemoryDB[MemoryUserRepo Datenbank]
        ReplicateClient[ReplicateClient AI Adapter]
    end

    %% WICHTIG: Infra implementiert Domain Interfaces
    InMemoryDB -.->|"Erfüllt Vertrag (implements)"| Interfaces
    ReplicateClient -.->|"Erfüllt Vertrag (implements)"| Interfaces

    %% Der Fluss geht weiter
    GenService -- "1. Guthaben prüfen via Interface" --> InMemoryDB
    GenService -- "2. Bild generieren via Interface" --> ReplicateClient

    %% --- Externe APIs ---
    ReplicateClient -- "API Call HTTP" --> ReplicateAPI["☁️ Replicate.com API"]

    %% --- Rückweg ---
    ReplicateAPI -- "Bild URL zurück" --> ReplicateClient
    ReplicateClient --> GenService
    GenService -- "Guthaben abziehen" --> InMemoryDB
    GenService -- "Ergebnis Erfolg/URL" --> Handlers
    Handlers -- "bot.send_photo()" --> Bot
    Bot --> TG_Server
    TG_Server --> User

    %% Styles
    classDef external fill:#f9f,stroke:#333,stroke-width:2px;
    classDef presentation fill:#e1f5fe,stroke:#0288d1;
    classDef application fill:#fff9c4,stroke:#fbc02d;
    classDef domain fill:#e8f5e9,stroke:#388e3c;
    classDef infrastructure fill:#ffe0b2,stroke:#f57c00;

    class User,TG_Server,ReplicateAPI external;
    class Bot,Handlers,BotInstance presentation;
    class GenService application;
    class Interfaces,Entities,note_interfaces domain;
    class InMemoryDB,ReplicateClient infrastructure;
