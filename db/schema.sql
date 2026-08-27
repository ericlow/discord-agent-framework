CREATE TABLE IF NOT EXISTS conversations (
    id         SERIAL PRIMARY KEY,
    messages   JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
