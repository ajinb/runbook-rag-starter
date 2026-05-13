# Runbook: checkout-svc latency spike

**Service:** `checkout-svc`
**SLO:** P99 latency < 300ms over 5 minutes
**Owner:** payments team

## Symptoms

- P99 latency over 300ms for more than 2 consecutive minutes
- Error rate may or may not be elevated; latency alone is the trigger
- Upstream `cart-svc` may also be affected (it calls checkout)

## Likely causes (in order of frequency)

1. **Stripe API slow path.** Stripe charge endpoint latency above 800ms; we have a 1.2s timeout.
2. **Database connection pool exhaustion.** `pgpool` for `checkout-svc` is bounded at 50; under load we sometimes wait for a connection.
3. **GC pause on the inventory cache.** Rare, but the JVM-based `inventory-svc` calls have occasionally introduced 1-2s pauses.

## Triage steps

1. Check the Stripe latency dashboard at the **payments / stripe-latency** Grafana board. If P95 > 600ms, that's the issue — escalate to the payments oncall.
2. Run `kubectl exec deploy/checkout-svc -- ./scripts/db-pool.sh` to see active connections. If > 45, scale the pool or restart the deployment.
3. Check `inventory-svc` GC logs in Loki for the last 15 minutes.

## Rollback / mitigation

- Stripe slow path: enable the `STRIPE_FAST_FAIL=1` env on `checkout-svc` (cuts the timeout to 600ms and shows a "try again" message to the user). Two-way door.
- Pool exhaustion: scale the deployment from 4 to 8 replicas via `kubectl scale`. Two-way door.
- GC pause: restart `inventory-svc`. Two-way door but disruptive.

## Do NOT do

- Do not increase the Stripe timeout above 1.2s without payments-team approval. We've had cascading deadlocks at 2s.
- Do not bypass the inventory check ("skip inventory" feature flag). It is a one-way door — overselling has accounting consequences.
