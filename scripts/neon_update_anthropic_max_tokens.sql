-- Neon / Postgres: max_tokens für Replicate Anthropic-Modelle auf 4000 begrenzen.
-- Ausführen z. B. in Neon SQL Editor oder: psql $DATABASE_URL -f scripts/neon_update_anthropic_max_tokens.sql
--
-- Setzt in input_schema.properties.max_tokens:
--   - maximum: 4000
--   - default: min(bisheriger default, 4000), sonst 4000

UPDATE ai_models
SET input_schema = jsonb_set(
  jsonb_set(
    input_schema,
    '{properties,max_tokens,maximum}',
    '4000'::jsonb,
    true
  ),
  '{properties,max_tokens,default}',
  to_jsonb(
    CASE
      WHEN (input_schema #>> '{properties,max_tokens,default}') ~ '^[0-9]+$'
        THEN LEAST(
          4000,
          (input_schema #>> '{properties,max_tokens,default}')::int
        )
      ELSE 4000
    END
  ),
  true
)
WHERE input_schema IS NOT NULL
  AND (input_schema -> 'properties') ? 'max_tokens'
  AND (
    LOWER(COALESCE(replicate_id, '')) LIKE '%anthropic%'
    OR LOWER(COALESCE(key, '')) LIKE '%anthropic%'
  );
