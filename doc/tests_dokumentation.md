# Test-Dokumentation – AZAMAT AI Bot

Vollständige technische Dokumentation des Test-Setups mit exakten Pfaden, Abläufen und Erweiterungshinweisen.

---

## 1. Übersicht

| Aspekt | Details |
|--------|---------|
| **Framework** | pytest 7.4+ |
| **Linting** | ruff (nur `tests/`) |
| **CI** | GitHub Actions (`.github/workflows/ci.yml`) |
| **Testanzahl** | 125 Unit-Tests in 17 Dateien |
| **Coverage** | Optional via `pytest-cov` |

---

## 2. Verzeichnisstruktur – exakte Pfade

```
flux-bot-azamat/
├── .github/workflows/ci.yml          # CI-Pipeline (Push/PR → main, develop)
├── pytest.ini                         # Pytest-Konfiguration (Root)
├── requirements.txt                   # Enthält: pytest, pytest-cov
└── tests/
    ├── conftest.py                    # Globale Fixtures + Env-Vars
    ├── test_config_settings.py        # Settings (config, START_CREDITS, optionale API-Keys)
    ├── test_database_transactions.py  # DatabaseManager update_credits → transactions
    ├── test_db_memory_repo.py         # InMemoryUserRepo
    ├── test_domain_entities.py        # AIModel, MediaFile, MediaType, User, GenerationResult
    ├── test_dynamic_adapter.py        # DynamicSchemaAdapter (build_input_payload, parse_output)
    ├── test_error_checks.py           # error_checks (URI, Rate-Limit, Technical)
    ├── test_flask_app.py              # Flask /, /api/strings, /api/shop_packages
    ├── test_generation_service_transactions.py  # GenerationService (update_credits, Sicherheit, Credits)
    ├── test_handlers_common.py        # get_context, set_context, clear_context (Dialog-State)
    ├── test_infrastructure_metrics.py # record_timing, get_stats
    ├── test_infrastructure_validator.py # InputValidator (sanitize, validate_safety)
    ├── test_prompt_engineer.py        # _truncate_fallback (LLM-Summarization Fallback)
    ├── test_utils_gimmicks.py         # get_random_tip
    ├── test_utils_media_utils.py      # detect_media_from_bytes (Magic Bytes)
    ├── test_utils_strings.py          # get_text, get_welcome, get_webapp_strings, daily_fallback
    ├── test_utils_temp_cleanup.py     # cleanup_temp_folder
    └── test_utils_telegram_init_data.py # validate_init_data
```

---

## 3. Ausführungsablauf – Pfad nachvollziehbar

### 3.1 Pytest-Start

1. **pytest** wird aufgerufen (CLI oder CI).
2. **`pytest.ini`** wird geladen:
   - `testpaths = tests` → Nur Ordner `tests/` wird gescannt
   - `python_files = test_*.py` → Nur Dateien, die mit `test_` beginnen
   - `python_functions = test_*` → Nur Funktionen, die mit `test_` beginnen
3. **`tests/conftest.py`** wird vor allen Testmodulen geladen.

### 3.2 conftest.py – Reihenfolge

```
tests/conftest.py
    │
    ├─ Modul-Load-Zeit:
    │  os.environ.setdefault("TELEGRAM_TOKEN", "test_fake_token_for_ci_12345")
    │  os.environ.setdefault("REPLICATE_API_TOKEN", "test_fake_replicate_for_ci_67890")
    │
    └─ pytest_configure(config):
       Setzt beide Env-Vars erneut, falls noch nicht gesetzt.
       → Voraussetzung für main.py / src.config.settings
```

**Warum nötig?**  
`main.py` importiert `src.config.settings`, das `Settings()` instanziiert und `TELEGRAM_TOKEN` sowie `REPLICATE_API_TOKEN` als Pflichtvariablen erwartet. Ohne diese Werte würde der Import fehlschlagen.

### 3.3 Test-Sammlung

Pytest sammelt alle `test_*.py` in `tests/` und führt sie aus. Die Reihenfolge ist nicht garantiert; Tests müssen unabhängig voneinander sein.

### 3.4 CI-Ablauf (GitHub Actions)

```
.github/workflows/ci.yml
    │
    ├─ Trigger: push / pull_request auf main, develop
    │
    ├─ Job: test (ubuntu-latest)
    │   ├─ actions/checkout@v4
    │   ├─ actions/setup-python@v5 (Python 3.11)
    │   ├─ pip cache (key: requirements.txt hash)
    │   ├─ pip install -r requirements.txt
    │   ├─ ruff check tests/
    │   ├─ pytest tests/ -v --tb=short
    │   └─ pytest tests/ ... --cov=src --cov-report=term-missing
```

---

## 4. Test-Dateien im Detail

### 4.1 tests/test_utils_strings.py

| Pfad (getestet) | Modul | Funktionen |
|-----------------|-------|------------|
| `src/utils/strings.py` | `src.utils.strings` | `get_text`, `get_welcome`, `get_webapp_strings`, `get_random_daily_fallback` |

**Imports:**
```python
from src.utils.strings import (
    get_text,
    get_welcome,
    get_webapp_strings,
    get_random_daily_fallback,
)
```

**Klassen und Tests:**

| Klasse | Test | Input | Erwartung |
|--------|------|-------|-----------|
| `TestGetText` | `test_existing_key_en` | `get_text("btn_back","en")`, `get_text("btn_back","de")` | "Back" in en, "Zurück" in de |
| | `test_existing_key_fallback_to_en` | `get_text("btn_back","xy")` | Ergebnis nicht leer (Fallback auf en) |
| | `test_unknown_key_returns_key` | `get_text("nonexistent_key_xyz","en")` | Rückgabe == `"nonexistent_key_xyz"` |
| | `test_nested_key_welcome` | `get_text("welcome","de")` | "AZAMAT" und "Kasachstan" im Text |
| `TestGetWelcome` | `test_with_name` | `get_welcome("en","Max")` | "Max" im Text |
| | `test_without_name_fallback` | `get_welcome("en",None)` | "there" oder "AZAMAT" im Text |
| | `test_empty_name_uses_fallback` | `get_welcome("de","   ")` | "du" oder "AZAMAT" im Text |
| | `test_all_locales_have_welcome` | `get_welcome(lang,"Test")` für en,de,ru,kk | AZAMAT im Text |
| `TestGetWebappStrings` | `test_returns_dict` | `get_webapp_strings("de")` | Rückgabe ist `dict` |
| | `test_contains_webapp_keys` | `get_webapp_strings("de")` | Keys: webapp_title, webapp_models, webapp_back |
| | `test_values_not_empty` | `get_webapp_strings("en")` | Alle Werte sind non-empty Strings |
| `TestGetRandomDailyFallback` | `test_returns_string` | `get_random_daily_fallback("en","User")` | Nicht-leerer String |
| | `test_contains_name_when_given` | `get_random_daily_fallback("en","Alice")` | "Alice" im Ergebnis |
| | `test_handles_empty_name` | `get_random_daily_fallback("de","")` | String (beliebig) |

**Erweiterung:** Neue String-Keys in `STRINGS` → Test für `get_text(key, lang)` hinzufügen. Neue Sprachen → `test_all_locales_have_welcome` erweitern.

---

### 4.2 tests/test_utils_gimmicks.py

| Pfad (getestet) | Modul | Funktion |
|-----------------|-------|----------|
| `src/utils/gimmicks.py` | `src.utils.gimmicks` | `get_random_tip` |

**Imports:**
```python
from src.utils.gimmicks import get_random_tip, TIPS_DICT
```

**Klassen und Tests:**

| Klasse | Test | Input | Erwartung |
|--------|------|-------|-----------|
| `TestGetRandomTip` | `test_returns_string` | `get_random_tip("de")` | Nicht-leerer String |
| | `test_german_tips_contain_keywords` | `get_random_tip("de")` (10x) | Jeder Tipp enthält "Tipp", "b>", "💡" oder "🚀" |
| | `test_unknown_lang_fallback_to_en` | `get_random_tip("xy")` | Ergebnis in `TIPS_DICT["en"]` |
| | `test_all_supported_languages` | `get_random_tip(lang)` für de,en,ru,kk | Tipp in TIPS_DICT[lang] bzw. fallback |

**Erweiterung:** Neue Sprache in `TIPS_DICT` → `test_all_supported_languages` anpassen.

---

### 4.3 tests/test_utils_telegram_init_data.py

| Pfad (getestet) | Modul | Funktion |
|-----------------|-------|----------|
| `src/utils/telegram_init_data.py` | `src.utils.telegram_init_data` | `validate_init_data` |

**Imports:**
```python
from src.utils.telegram_init_data import validate_init_data
```

**Klassen und Tests:**

| Test | Input | Erwartung |
|------|-------|-----------|
| `test_empty_init_data_returns_none` | `validate_init_data("","any_token")` | `None` |
| `test_empty_token_returns_none` | `validate_init_data("user=...","")` | `None` |
| `test_both_empty_returns_none` | `validate_init_data("","")` | `None` |
| `test_invalid_hash_returns_none` | `validate_init_data("user=...&hash=invalid_hash_value","...")` | `None` |
| `test_missing_hash_returns_none` | `validate_init_data("user=...","...")` (ohne hash) | `None` |
| `test_malformed_json_returns_none` | `validate_init_data("user=not_valid_json&hash=abc","token")` | `None` |

**Hinweis:** Ein Test für *gültige* initData würde echte HMAC-Berechnung mit echtem Bot-Token erfordern und ist nicht trivial.

**Erweiterung:** Weitere Edge-Cases (z.B. leerer user-Parameter) als neue Testmethoden ergänzen.

---

### 4.4 tests/test_domain_entities.py

| Pfad (getestet) | Modul | Entitäten |
|-----------------|-------|-----------|
| `src/domain/entities.py` | `src.domain.entities` | AIModel, MediaFile, User, GenerationResult |

**Imports:**
```python
from src.domain.entities import (
    AIModel, MediaFile, MediaType, User, GenerationResult,
)
```

**Klassen und Tests:**

| Klasse | Test | Logik |
|--------|------|-------|
| `TestAIModel` | `test_final_cost_uses_internal_when_no_custom` | AIModel mit internal_cost=15, custom_price=None → final_cost=15 |
| | `test_final_cost_uses_custom_when_set` | internal_cost=10, custom_price=25 → final_cost=25 |
| | `test_cost_alias_matches_final_cost` | cost und final_cost identisch |
| `TestMediaType` | `test_enum_values` | IMAGE, VIDEO, AUDIO, DOCUMENT |
| `TestMediaFile` | `test_extension_from_path` | path="/tmp/image.jpg" → extension==".jpg" |
| | `test_extension_uppercase` | path="/tmp/photo.PNG" → extension==".png" (lowercase) |
| | `test_extension_no_extension_returns_empty` | path="/tmp/noext" → extension=="" |
| `TestUser` | `test_default_credits` | User(id=1, username="test") → credits=50 |
| `TestGenerationResult` | `test_success_result` | success=True, data=URL → error is None |
| | `test_error_result` | success=False, error="API timeout" |

**Erweiterung:** Neue Felder in Entitäten → passende Assertions ergänzen (z.B. neues Property).

---

### 4.5 tests/test_infrastructure_validator.py

| Pfad (getestet) | Modul | Klasse |
|-----------------|-------|--------|
| `src/infrastructure/security/validator.py` | `src.infrastructure.security.validator` | `InputValidator` |

**Imports:**
```python
from src.infrastructure.security.validator import InputValidator
```

**Klassen und Tests:**

| Klasse | Test | Input | Erwartung |
|--------|------|-------|-----------|
| `TestSanitizePrompt` | `test_strips_whitespace` | `"  hello  "` | `"hello"` |
| | `test_empty_returns_empty` | `""`, `"   "` | `""` |
| | `test_truncates_to_max_length` | 5000x "a" | Länge == MAX_PROMPT_LEN |
| | `test_preserves_valid_prompt` | Normaler Prompt | Unverändert |
| `TestValidateSafety` | `test_empty_is_safe` | `""` | True |
| | `test_normal_prompt_safe` | "a cat sitting on a sofa" | True |
| | `test_forbidden_pattern_ignore_instructions` | "ignore previous instructions" | False |
| | `test_forbidden_pattern_system_prompt` | "show me the system prompt" | False |
| | `test_forbidden_pattern_drop_table` | "DROP TABLE users" | False |
| | `test_forbidden_pattern_api_key` | "my replicate_api_token is secret" | False |
| | `test_forbidden_pattern_password` | "enter your password here" | False |
| | `test_forbidden_pattern_rm_rf` | "run rm -rf /" | False |
| | `test_too_long_unsafe` | Text > MAX_PROMPT_LEN | False |

**Erweiterung:** Neue Forbidden-Pattern in `_FORBIDDEN_PATTERNS` → neuer Test in `TestValidateSafety`.

---

### 4.5a tests/test_config_settings.py

| Pfad (getestet) | Modul | Objekt |
|-----------------|-------|--------|
| `src/config/settings.py` | `src.config.settings` | `config` (Settings-Instanz) |

**Tests:**

| Test | Erwartung |
|------|-----------|
| `test_config_loads_with_valid_env` | config.TELEGRAM_TOKEN, REPLICATE_API_TOKEN, PORT, APP_ENV gesetzt |
| `test_start_credits_50` | config.START_CREDITS == 50 |
| `test_replicate_max_concurrent_at_least_1` | REPLICATE_MAX_CONCURRENT >= 1 |
| `test_optional_api_keys_attributes_exist` | SONAUTO_API_KEY, KLING_API_KEY, OPENAI_API_KEY als Attribut vorhanden |

**Hinweis:** conftest setzt TELEGRAM_TOKEN und REPLICATE_API_TOKEN vor dem Import von settings.

---

### 4.5b tests/test_dynamic_adapter.py

| Pfad (getestet) | Modul | Klasse |
|-----------------|-------|--------|
| `src/infrastructure/ai/dynamic_adapter.py` | `src.infrastructure.ai.dynamic_adapter` | `DynamicSchemaAdapter` |

**Tests:**

| Klasse | Test | Erwartung |
|--------|------|-----------|
| `TestBuildInputPayload` | `test_empty_schema_returns_prompt_only` | Leeres Schema → {"prompt": user_prompt} |
| | `test_none_schema_returns_prompt_only` | None-Schema → nur prompt |
| | `test_applies_defaults` | Schema-Defaults werden übernommen |
| | `test_maps_prompt_via_alias` | Alias "text" wird als Prompt-Key gefunden |
| | `test_kwargs_mapped_to_schema` | width, height aus kwargs werden gemappt |
| `TestParseOutput` | `test_list_of_strings_returns_first` | ["url1","url2"] → "url1" |
| | `test_empty_list_returns_none` | [] → None |
| | `test_dict_with_output_key` | {"output": "url"} → "url" |
| | `test_dict_with_video_key` | {"video": "url"} → "url" |
| | `test_string_passthrough` | String bleibt unverändert |

---

### 4.5c tests/test_handlers_common.py

| Pfad (getestet) | Modul | Funktionen |
|-----------------|-------|------------|
| `src/presentation/telegram/handlers/common.py` | `src.presentation.telegram.handlers.common` | `get_context`, `set_context`, `clear_context` |

**Tests:**

| Test | Erwartung |
|------|-----------|
| `test_get_context_empty_returns_empty_dict` | Frischer User → {} |
| `test_set_and_get_context` | set_context speichert, get_context liefert Kopie |
| `test_get_returns_copy` | Modifikation der Rückgabe ändert nicht den gespeicherten Zustand |
| `test_clear_context_removes_data` | clear_context entfernt Eintrag |
| `test_clear_nonexistent_is_safe` | clear bei nicht vorhandenem User löst keine Ausnahme aus |

---

### 4.5d tests/test_prompt_engineer.py

| Pfad (getestet) | Modul | Funktion |
|-----------------|-------|----------|
| `src/infrastructure/ai/replicate/prompt_engineer.py` | `src.infrastructure.ai.replicate.prompt_engineer` | `_truncate_fallback` |

**Tests:**

| Test | Erwartung |
|------|-----------|
| `test_short_text_unchanged` | Kurzer Text bleibt unverändert |
| `test_none_or_empty` | None, "", "   " → leerer String |
| `test_long_text_truncated` | Text > max_len → Kürzung + "..." |
| `test_custom_max_len` | max_len-Parameter wird berücksichtigt |

---

### 4.5e tests/test_utils_media_utils.py

| Pfad (getestet) | Modul | Funktion |
|-----------------|-------|----------|
| `src/utils/media_utils.py` | `src.utils.media_utils` | `detect_media_from_bytes` |

**Tests:** Magic-Byte-Erkennung für PNG, JPEG, GIF, WebP, MP4, WebM, AVI, MP3, WAV, OGG, FLAC. Leere Daten → Fallback image/.png.

---

### 4.5f tests/test_utils_temp_cleanup.py

| Pfad (getestet) | Modul | Funktion |
|-----------------|-------|----------|
| `src/utils/temp_cleanup.py` | `src.utils.temp_cleanup` | `cleanup_temp_folder` |

**Tests:** Nicht existierender Ordner → 0; alte Dateien werden gelöscht; neue Dateien bleiben; Unterordner werden ignoriert. Nutzt `time.sleep(1.1)` für Alter-Simulation.

---

### 4.6 tests/test_infrastructure_metrics.py

| Pfad (getestet) | Modul | Funktionen |
|-----------------|-------|------------|
| `src/infrastructure/metrics.py` | `src.infrastructure.metrics` | `record_timing`, `get_stats` |

**Imports:**
```python
from src.infrastructure.metrics import record_timing, get_stats
```

**Tests:**

| Test | Ablauf | Erwartung |
|------|--------|-----------|
| `test_record_and_get_stats` | record_timing("test_op", 0.5) → get_stats() | "test_op" in stats, count>=1, last=0.5 |
| `test_multiple_records_accumulate` | 2x record_timing("acc_test", 1.0/2.0) | count>=2, total>=3.0 |
| `test_get_stats_returns_copy` | get_stats() → Modifikation von s1 → erneut get_stats() | Original unverändert (Kopie) |

**Hinweis:** Metriken sind global; andere Tests könnten dieselben Keys nutzen. Namen wie "test_op", "acc_test", "copy_test" sind spezifisch gewählt.

**Erweiterung:** Weitere Metrik-Funktionen → analog testen (record + get + Assertions).

---

### 4.7 tests/test_error_checks.py

| Pfad (getestet) | Modul | Funktionen |
|-----------------|-------|------------|
| `src/presentation/telegram/handlers/gen/error_checks.py` | `src.presentation.telegram.handlers.gen.error_checks` | `is_uri_too_large`, `is_rate_limit`, `is_technical_error` |

**Imports:**
```python
from src.presentation.telegram.handlers.gen.error_checks import (
    is_uri_too_large, is_rate_limit, is_technical_error,
)
```

**Import-Kette:** Beim Import von `error_checks` wird `gen/__init__.py` geladen → benötigt `telebot` (pyTelegramBotAPI). Daher müssen alle Dependencies aus `requirements.txt` installiert sein.

**Klassen und Tests:**

| Klasse | Test | Input | Erwartung |
|--------|------|-------|-----------|
| `TestIsUriTooLarge` | `test_414_in_message` | "Error 414 Request-URI Too Large" | True |
| | `test_uri_too_large_phrase` | "request-uri too large" | True |
| | `test_normal_error_false` | "Something went wrong" | False |
| `TestIsRateLimit` | `test_429_detected` | "429 Too Many Requests" | True |
| | `test_throttle_detected` | "throttled" | True |
| | `test_rate_limit_phrase` | "rate limit exceeded" | True |
| | `test_empty_false` | "" | False |
| | `test_normal_error_false` | "Internal server error" | False |
| `TestIsTechnicalError` | `test_credits_not_technical` | "not enough credits" | False |
| | `test_nsfw_not_technical` | "NSFW content detected" | False |
| | `test_timeout_is_technical` | "Connection timeout" | True |
| | `test_empty_false` | "" | False |

**Erweiterung:** Neue Fehlermuster in den Funktionen → passende Tests ergänzen.

---

### 4.8 tests/test_db_memory_repo.py

| Pfad (getestet) | Modul | Klasse |
|-----------------|-------|--------|
| `src/infrastructure/db/memory_repo.py` | `src.infrastructure.db.memory_repo` | `InMemoryUserRepo` |

**Imports:**
```python
from src.infrastructure.db.memory_repo import InMemoryUserRepo
```

**Tests:**

| Test | Ablauf | Erwartung |
|------|--------|-----------|
| `test_get_user_creates_guest_if_not_exists` | get_user(99999) ohne vorherigen add | User mit username="Guest", credits=50 |
| `test_add_user_if_not_exists` | add_user_if_not_exists(1,"Alice") → get_user(1) | username="Alice", credits=50 |
| `test_add_user_idempotent` | add(1,"Alice"), add(1,"Bob") → get_user(1) | username="Alice" (nicht überschrieben) |
| `test_update_credits_existing_user` | add(1,"Alice"), update_credits(1,10) | get_user_credits(1)==60 |
| `test_update_credits_new_user_creates_with_default_plus_amount` | update_credits(999,-5) ohne add | credits=45 (50+(-5)) |

**Erweiterung:** Neue Repo-Methoden → Tests analog zu bestehenden Mustern.

---

### 4.9 tests/test_generation_service_transactions.py (erweitert)

| Pfad (getestet) | Modul | Klasse |
|-----------------|-------|--------|
| `src/application/services.py` | `src.application.services` | `GenerationService` |

**Tests:** Erfolg → update_credits; no_charge → kein update_credits; Fehlschlag → kein update_credits; **unsafe Prompt** → Ablehnung, kein ai.generate; **zu wenig Credits** → Ablehnung, kein ai.generate.

---

### 4.10 tests/test_flask_app.py

| Pfad (getestet) | Modul | Objekt |
|-----------------|-------|--------|
| `main.py` | `main` | `app` (Flask) |

**Fixture:**
```python
@pytest.fixture
def client():
    from main import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
```

**Import-Reihenfolge wichtig:**  
`main` wird erst importiert, nachdem `conftest.py` die Env-Vars gesetzt hat. Sonst würde `config = Settings()` in `src.config.settings` fehlschlagen.

**Klassen und Tests:**

| Klasse | Test | Request | Erwartung |
|--------|------|---------|-----------|
| `TestHealthCheck` | `test_root_returns_200` | GET / | status_code=200, "ONLINE" in Body |
| | `test_root_returns_text` | GET / | "System Status" oder "ONLINE" im Body |
| `TestApiStrings` | `test_strings_default_lang` | GET /api/strings | 200, JSON mit Key "webapp_title" |
| | `test_strings_lang_param` | GET /api/strings?lang=en | 200, dict |
| | `test_strings_invalid_lang_fallback_de` | GET /api/strings?lang=xy | 200 |
| `TestApiShopPackages` | `test_shop_packages_returns_200_and_list` | GET /api/shop_packages | 200, packages-Liste |
| | `test_shop_packages_structure` | GET /api/shop_packages | Jedes Paket: label, credits, price |

**Erweiterung:** Neue Endpoints in `main.py` → neue Testklasse mit `client.get()`/`post()` und Assertions.

---

## 5. Befehle – Referenz

| Aktion | Befehl |
|--------|--------|
| Alle Tests | `pytest tests/ -v` |
| Mit Coverage | `pytest tests/ -v --cov=src --cov-report=term-missing` |
| Einzelne Datei | `pytest tests/test_utils_strings.py -v` |
| Einzelner Test | `pytest tests/test_utils_strings.py::TestGetText::test_existing_key_en -v` |
| Ruff (Tests) | `ruff check tests/` |

---

## 6. Neue Tests hinzufügen – Checkliste

1. **Datei:** `tests/test_<modulname>.py` (z.B. `test_services.py`)
2. **Format:** Klasse mit `Test`-Präfix, Methoden mit `test_`-Präfix
3. **Import:** Getestetes Modul importieren
4. **Fixture bei Bedarf:** Wenn Flask/DB nötig → Fixture in `conftest.py` oder lokal definieren
5. **Env-Vars:** Bei Tests, die `main` oder `config` brauchen → `conftest.py` stellt sie bereit
6. **Linting:** `ruff check tests/test_<modulname>.py` ausführen
7. **Lauf:** `pytest tests/test_<modulname>.py -v`

---

## 7. Abhängigkeiten – Pfad-Matrix

| Test-Datei | Benötigt (direkt/indirekt) |
|------------|----------------------------|
| test_utils_* | Keine Env-Vars |
| test_domain_entities | Keine |
| test_infrastructure_validator | Keine |
| test_infrastructure_metrics | Keine |
| test_db_memory_repo | Keine |
| test_error_checks | telebot (via gen/__init__.py) |
| test_flask_app | TELEGRAM_TOKEN, REPLICATE_API_TOKEN (für main → config) |
| test_generation_service_transactions | Keine (Mock) |
| test_database_transactions | Mock psycopg2 |
| test_config_settings | conftest setzt Env-Vars |
| test_dynamic_adapter | Keine |
| test_handlers_common | Keine |
| test_prompt_engineer | Keine |
| test_utils_media_utils | Keine |
| test_utils_temp_cleanup | tempfile, time.sleep für Alter-Simulation |

---

## 8. Übersicht: Getestete vs. nicht getestete Module

| Getestet | Nicht getestet (z.B. wegen externer Dependencies) |
|----------|---------------------------------------------------|
| utils (strings, gimmicks, media_utils, temp_cleanup, telegram_init_data) | main.py (nur app-Flask), handlers (nur common, error_checks) |
| domain.entities, infrastructure.validator, metrics, db.memory_repo | replicate.clients, unified_client, kling_client, sonauto_client |
| application.services (GenerationService) | payment_handler, menu_handler, gen_handlers |
| config.settings, dynamic_adapter, prompt_engineer._truncate_fallback | database.DatabaseManager (nur update_credits gemockt) |

---

## 9. Transaktionen (Neon)

Die Tests `test_generation_service_transactions` und `test_database_transactions` prüfen, dass jede erfolgreiche Generierung eine Zeile in der `transactions`-Tabelle erzeugt. Bei jeder Abbuchung loggt `database.py`:

`Transaction recorded: user_id=X amount=Y reason=Z`

Falls keine Transaktion erscheint: Render-Logs prüfen – ist diese Zeile vorhanden? Wenn ja, aber keine Zeile in Neon: DATABASE_URL oder Neon-Branch prüfen. Wenn nicht: anderer Code-Pfad (z.B. no_charge) oder vorzeitiger Abbruch.

---

## 10. Bekannte Einschränkungen

- **Ruff:** Es wird nur `tests/` gelintet, nicht das gesamte Projekt.
- **Coverage:** Es gibt keinen Mindest-Coverage-Wert; der Report dient der Orientierung.
- **Flask:** Endpoints wie `/api/webapp_action` oder `/api/models` brauchen `_db_instance`/`_bot_instance` und werden hier nicht getestet.
- **initData:** Es gibt keinen Test mit gültigem HMAC (würde echten Bot-Token erfordern).
