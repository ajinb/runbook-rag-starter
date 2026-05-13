# Runbook: primary Postgres failover

**Service:** `payments-db` (Postgres 16, primary + 2 replicas)
**SLO:** N/A — this is recovery for a failure already in progress.
**Owner:** platform team

## When to run this

You're here because:

- `pg_isready` is failing against the primary, OR
- The primary's host has been unreachable for > 60 seconds, OR
- The application-side circuit breaker around the DB has been open for > 5 minutes

## Pre-checks

1. Confirm it really is the primary. `kubectl get pod payments-db-0 -o wide` should show the node name. If the pod is `Running` but unreachable, this might be a network partition, not a DB failure.
2. Check replica lag on `payments-db-1` and `payments-db-2`. Use `SELECT now() - pg_last_xact_replay_timestamp();` against each. A replica with > 30 seconds of lag is not a safe promotion target.

## Failover procedure

1. **Pick the promotion target.** Whichever replica has the lowest lag and is in the same AZ as the failed primary's expected replacement.
2. **Promote.** `kubectl exec payments-db-1 -- patronictl failover --candidate payments-db-1 --force`. Patroni handles the wal_position check and the role flip.
3. **Verify.** `kubectl exec payments-db-1 -- psql -c "SELECT pg_is_in_recovery();"` should return `f`.
4. **Update the application.** The `payments-db-primary` Service selector should already point at the new pod via Patroni's labels. If not, edit it manually.
5. **Bring the old primary back as a replica** once the host is reachable. `patronictl reinit payments-db-0`.

## Post-mortem reminders

- Don't blame Patroni. It's doing what it's told. If the failover was unexpected, the root cause is upstream — host, network, or storage.
- Record actual lag at promotion time. If we lost transactions, we need to know.

## Do NOT do

- Do not run `pg_ctl promote` directly. Patroni won't know about the role change and the cluster will fight itself.
- Do not delete the old primary's data volume until at least one full backup of the new primary has succeeded. One-way door.
