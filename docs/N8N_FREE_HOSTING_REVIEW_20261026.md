# Free n8n hosting assessment — 26 October 2026

Research only. No account created, payment information entered, resource
provisioned, public endpoint exposed, credential changed or automation activated.
The verified local integration checkpoint is 2daef20. Its live test and evidence
remain valid; this investigation does not repeat them.

## Recommendation

**Oracle Cloud Always Free is the closest fit among the options checked for a
zero-cost, independently running DefectRAG n8n demonstration. It is conditional,
not a promise of uninterrupted production availability.** Capacity can be
unavailable, and Oracle may reclaim idle compute. A lightly used notification
server is relevant to that idle policy; do not generate artificial load to evade it.
[Oracle resource limits and idle policy](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

Current Oracle documentation lists a total A1 Always Free allowance equivalent to
2 OCPUs and 12 GB RAM, plus 200 GB combined boot/block storage in the home region.
These are current documented limits, not the older 4 OCPU / 24 GB figures still
found in tutorials. Availability and the actual console entitlement must be checked
before provisioning. [Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

Oracle requires card verification and can place a temporary authorization hold.
Its Free Tier documentation says the card is not charged unless the account is
upgraded. Free Trial credits are separate from Always Free resources. Retain a
Free Tier account, do not upgrade to Pay As You Go, and provision only explicitly
Always Free eligible resources after reviewing the console estimate.
[Signup FAQ](https://www.oracle.com/cloud/free/faq/),
[trial versus Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm).

## Comparison

| Option | Verified limitation | Assessment for this application |
| --- | --- | --- |
| Oracle Always Free VM | Persistent block storage and ongoing free compute within limits; availability and idle reclamation constraints; card verification | Best candidate to investigate first. Server management, backups and security remain our responsibility. |
| Render Free | Sleeps after 15 minutes without traffic; ephemeral local filesystem; no free persistent disks; its free PostgreSQL expires after 30 days | Appropriate for disposable demos, unsuitable as the straightforward persistent unattended n8n host required here. An external database alone does not keep its scheduler running while asleep. [Render](https://render.com/docs/free). |
| Koyeb Free | 512 MB RAM / 0.1 vCPU; scales to zero after one hour without traffic; no volumes or worker services | Poor fit for persistent n8n and unattended deadline scheduling. [Koyeb](https://www.koyeb.com/docs/reference/instances). |
| Railway Free | Initial $5 / 30-day trial, then $1 monthly non-rolling credit | A credit allowance, not a guaranteed continuously free n8n allocation. Do not assume it covers a full month of this workload. [Railway](https://docs.railway.com/pricing/free-trial). |
| Google Cloud e2-micro | Eligible US-region VM hours and 30 GB standard disk have a free allowance; public IPv4 is separately priced at $0.005/hour with only one free hour/month in the cited network table | Not a straightforward $0 public-IPv4 deployment. IPv6/alternate ingress would need a separate compatibility and cost review. [Free allowance](https://docs.cloud.google.com/free/docs/free-cloud-features), [IPv4 pricing](https://cloud.google.com/vpc/network-pricing). |
| n8n Cloud | No ongoing free plan after the trial | Convenient managed service, outside the requested ongoing-free scope. [n8n trial FAQ](https://support.n8n.io/article/how-do-i-cancel-my-trial). |
| Hugging Face free hardware | Sleeps when unused; default local disk is nonpersistent | Preserve the existing DefectRAG Space; do not add a scheduler or credential database there. [Spaces lifecycle/storage](https://huggingface.co/docs/hub/spaces-overview). |

These assessments are engineering conclusions drawn from the linked provider
limits. No account-specific eligibility, available capacity, uptime or cost has
been verified by deployment. Among the checked offers, none justifies claiming
guaranteed production uptime at no cost.

## Proposed Oracle setup, not yet authorized or provisioned

1. One A1 Linux VM, initially 1 OCPU / 6 GB RAM and a 50 GB boot volume, within
   the account's actual Always Free entitlement. This is a proposed small-workload
   allocation, not a measured performance result. Check the tested n8n image's ARM
   support before choosing A1; do not silently upgrade n8n to make it fit.
2. Pin the already tested n8n version. Run its required workflow services and a
   dedicated PostgreSQL database with durable volumes. Do not use the DefectRAG
   application's Supabase database as n8n's internal credential/workflow database.
   Back up both n8n data/encryption material and its database, then restore-test
   them. n8n documents persistent data and Postgres configuration in its
   [Docker documentation](https://docs.n8n.io/hosting/installation/docker/).
3. Use a free DNS hostname if a purchased domain is unavailable. Duck DNS offers
   free dynamic DNS; hostname availability must be checked after approval.
   DNS is not a server or TLS certificate. A reverse proxy such as Caddy can
   obtain/renew a publicly trusted certificate once DNS and inbound ports are
   correctly configured. [Duck DNS](https://www.duckdns.org/faqs.jsp),
   [Caddy HTTPS requirements](https://caddyserver.com/docs/automatic-https).
4. Expose only the authenticated production webhook needed by Supabase. Keep the
   editor restricted and database/container ports private. Set the correct public
   webhook URL, proxy configuration and Asia/Kuala_Lumpur schedule timezone.
5. Reuse reviewed production workflow logic, not the QA sink workflow or its keys.
   Owner enters distinct production credentials privately; n8n receives no Supabase
   service-role key. Keep delivery and schedules inactive during setup.
6. Test backups, certificate renewal, restart persistence, actual supervisor email,
   deadline reminders, overdue alerts, provider failures, revoked recipient handling
   and operation while the Windows laptop is off. Confirm any SMTP port restrictions
   before selecting the mail transport; do not assume existing Gmail SMTP works
   from the chosen host.
7. Before activation, separately approve a way to quarantine retained synthetic QA
   events. The closed QA case's latest updated notification must not accidentally
   become real supervisor mail. Preserve its history rather than deleting records.
8. Request explicit production activation approval only after the hosted tests pass.
   Keep existing Developer registration Cron/Edge/Resend notifications unchanged.

## Exact next step

Decide whether Oracle's private card verification, capacity risk and idle reclamation
are acceptable for a portfolio demonstration. If approved, the owner creates ONE
Free Tier account privately and stops at the console, before provisioning or
upgrading. Verify actual Always Free availability and a zero-cost estimate next.
Do not enter card details, passwords or tokens in chat. If these conditions are
unacceptable, retain the verified local demonstration; a different hosting budget
or an already available always-on machine will be needed for dependable unattended
operation. No hosting decision changes the completed local test result.
