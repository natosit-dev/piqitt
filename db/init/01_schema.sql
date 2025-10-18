CREATE TABLE IF NOT EXISTS bundle (
  bundle_id TEXT PRIMARY KEY,
  source_system TEXT,
  received_at TIMESTAMP DEFAULT now()
);
