# Runbook: TLS certificate renewal

**Component:** Ingress wildcard cert (`*.cloudandsre.com`)
**Provider:** Let's Encrypt via cert-manager
**Owner:** platform team

## Normal flow (no action needed)

cert-manager auto-renews the wildcard 30 days before expiry via the ACME DNS-01 challenge against our Namecheap DNS API. The `Certificate` resource is `cert-manager.io/v1` with `secretName: wildcard-tls`. Renewal is fully automated.

You should only see this runbook because something failed.

## Symptoms

- Prometheus alert `CertificateExpiringSoon` firing (< 14 days to expiry).
- `kubectl describe cert wildcard-tls -n cert-manager` shows `Status: False` and a `Reason` other than `Ready`.
- Browser shows a cert warning on `cloudandsre.com`.

## Triage

1. **Read the cert-manager events.** `kubectl describe cert wildcard-tls -n cert-manager` will tell you exactly which step of the ACME flow failed (order creation, challenge, DNS propagation, finalization).
2. **Verify the DNS API is reachable.** The Namecheap API has had IP-allowlist issues. Test from inside the cluster: `kubectl run dns-test --rm -it --image=curlimages/curl -- curl -v https://api.namecheap.com`.
3. **Check rate limits.** Let's Encrypt allows 50 certs per registered domain per week. If we've been thrashing the renewal, we may be limited.

## Manual fix (only if cert-manager is stuck)

1. Force a re-issue: `kubectl annotate cert wildcard-tls -n cert-manager cert-manager.io/force-issue=true --overwrite`.
2. If that fails, delete the `CertificateRequest` and let cert-manager re-create it: `kubectl delete certificaterequest -n cert-manager -l cert-manager.io/certificate-name=wildcard-tls`.

## Do NOT do

- Do not delete the `wildcard-tls` Secret. That's the live cert. Deleting it takes the site down until a fresh issuance completes.
- Do not issue a manual cert from the staging Let's Encrypt environment unless you also remember to switch back. Browsers reject staging certs.
