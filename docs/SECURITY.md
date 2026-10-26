# Security and privacy

## Identity and Staff approval

Supabase Authentication owns identity, password recovery, sessions and native TOTP.
DefectRAG does not implement its own OTP generator or verifier. Email confirmation
and registration do not grant Staff privileges. An applicant submits a Pending
access request; only an active Developer with native AAL2 can approve, reject or
revoke it. Applicants cannot choose a role or approve themselves.

Protected operations check current membership and required assurance in backend
code, database functions, RLS and private storage policies. Hiding a page is not an
authorization boundary. Completing guided practice grants no real access.

## Data boundaries

- **Personal:** private to the authenticated owner, with versioned synchronization.
- **Team:** a separate copy created by explicit sharing; visible to authorized Staff.
- **Gallery:** a separate public copy, published with explicit consent.
- **Guest demo:** isolated temporary/local history, not an authenticated cloud account.
- **Guided practice:** temporary in-memory teaching state; no real record writes,
  model run, approval, sharing, notification or cloud-role change.

Original images and heatmaps need the appropriate access check. Public publication
can leave visible identifying details inside a photograph even when metadata is
removed. Never publish a private photograph simply because its file metadata was
sanitized. Notes and later Personal conversations are not automatically added to
an existing Team copy.

## Corrective Actions

A model anomaly flag alone is insufficient. A structured Team review must qualify
as a reviewed/rejected defect, followed by explicit human confirmation. Cases
have assignments, due dates, version checks and audited transitions. Only the
current owner, supervisor or an approved Developer can edit after required MFA.
Other authorized Staff retain read access to cases available within their Team
scope. These case-specific restrictions do not remove permitted Personal
inspection, synchronization, explicit sharing or Team review abilities.

## Safe MFA activation and recovery

For a new installation, keep registration and mandatory-MFA switches off while
bootstrapping the existing Developer identity. Preserve a private verified backup
and recovery plan. Enroll and verify native TOTP for the Developer, confirm AAL2
access and a separate account-denial check, then enable enforcement only after
explicit administrative review. Test recovery redirects and email delivery before
opening registration. Do not use a password reset as an MFA bypass or silently
remove a verified factor. Loss of an authenticator needs an authorized recovery
procedure. Existing activated installations should not disable their protections
to follow a fresh-install example.

Revocation must deny new protected operations using current membership checks.
Already-downloaded material cannot be recalled, and previously issued signed URLs
may remain usable until expiration. Revoke before issuing new protected content;
do not describe revocation as retroactive deletion of all copies.

## Secrets and automation

Only the public URL/publishable key can enter the frontend. Privileged Supabase,
worker, callback, SMTP and provider secrets stay server-side. Use distinct,
authenticated worker and callback credentials and bounded event permissions.
Notification workers claim durable outbox entries, validate responses, apply
retry/dead-letter rules and prevent duplicate side effects. Do not convert an
uncertain external send into a successful delivery or blindly replay it.

n8n manages notifications, not Staff approval, OTP verification or permission
grants. Its outage must not bypass authorization, change approval state or block
ordinary sign-in. A saved case is separate from mail delivery. Real unattended
Corrective Action delivery is not activated by this source repository.

## Application limits

Approved Staff can submit conversation answers without model-provenance
attestation. Citation validation provides traceability, not guaranteed entailment.
Anomaly scores are distances, not defect probabilities. Heatmaps are coarse
localization, not a supervised defect diagnosis. Previously confirmed integration
tests do not replace a security review for a new deployment.

Keep private database backups, raw traces, JWTs, signed links and account-specific
QA material outside GitHub. The public exporter uses a documentation allowlist;
internal progress remains in the private development archive.
