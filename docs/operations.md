# Operations

## Runtime checks

- Liveness is available at `/health/live`; readiness is available at `/health/ready`.
- Prometheus-compatible request counters and latency samples are available at `/metrics`.
- Correlation and trace identifiers are returned on every request response.
- `redact_pii` must be applied before writing user content to logs, traces, exports, or evaluation fixtures.

## Delivery and recovery

Run migrations as a release job with `alembic upgrade head`. Outbox records are replayable by event ID and inbox consumers must retain their idempotency key. Production deployments must provide `DATABASE_URL`, rotate `JWT_SECRET`, use managed PostgreSQL backups/PITR, and verify tenant isolation before enabling external providers.