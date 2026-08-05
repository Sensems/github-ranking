CREATE TABLE IF NOT EXISTS repos (
  repo_id BIGINT PRIMARY KEY,
  repo_name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  stars INT NOT NULL,
  forks INT NOT NULL,
  language TEXT,
  html_url TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  readme_hash TEXT,
  backfilled_365 DATE,
  updated_at DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
  repo_id BIGINT NOT NULL REFERENCES repos(repo_id),
  date DATE NOT NULL,
  stars INT NOT NULL,
  forks INT NOT NULL,
  PRIMARY KEY (repo_id, date)
);

CREATE TABLE IF NOT EXISTS readmes (
  repo_id BIGINT PRIMARY KEY REFERENCES repos(repo_id),
  hash TEXT NOT NULL,
  excerpt TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summaries (
  repo_id BIGINT PRIMARY KEY REFERENCES repos(repo_id),
  readme_hash TEXT,
  summary JSONB NOT NULL,
  generated_at DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS leaderboards (
  type TEXT PRIMARY KEY,
  generated_at DATE,
  items JSONB NOT NULL DEFAULT '[]'::jsonb
);
