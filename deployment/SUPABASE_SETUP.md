# Connect the staff workspace — no project has been created yet

The application does not include a cloud account, project, credentials or a
provisioned database. Its Supabase integration is setup-ready; hosted auth,
storage and row-level policies cannot be verified until your own project exists.
Use an eligible Free plan and check its current quotas. No paid resource is
automatically created by these files.

## 1. Create your project

Sign in at https://supabase.com/dashboard and create a project in your organisation.
Choose its region and keep the database password private. Account signup, billing
and acceptance of service terms remain under your control.

## 2. Install the schema and approve staff

Open SQL Editor and run `deployment/supabase.sql`. It creates:

- An explicit staff allowlist with `staff` and `developer` roles.
- Shared inspection snapshots and saved conversations.
- Append-only staff review notes and a developer-visible archive/restore audit.
- A private `team-inspections` storage bucket, with staff-only reads and
  owner-folder uploads; no browser delete/update permission.
- Row-level security that prevents anonymous/non-staff reads and role escalation.

In Authentication > Users, create or invite your own account and colleagues.
For each approved user, copy its auth UUID and run this in SQL Editor:

```sql
insert into public.staff_members(user_id,display_name,role)
values ('YOUR_AUTH_USER_UUID','Your name','developer');
-- Colleagues use role 'staff', not 'developer'.
```

Do not enable automatic staff membership for arbitrary public signups. This
schema represents one organisation's shared workspace, not multiple companies.

## 3. Add the public connection settings

Find Project URL and publishable key in the project Connect/API settings.
Edit `frontend/public/config.js` for source builds, or `config.js` in an extracted
static build. Add only these public values:

```javascript
window.DEFECTRAG_PUBLIC_CONFIG = {
  supabaseUrl: 'https://YOUR_PROJECT.supabase.co',
  supabasePublishableKey: 'YOUR_PUBLISHABLE_OR_ANON_KEY'
};
```

Never put a service-role/secret key or database password in frontend files.
For source-based Vercel/Render builds you can instead configure
`VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`, then rebuild.

In Authentication URL Configuration, set your dashboard Site URL and permitted
password-reset redirects. For local testing allow `http://127.0.0.1:8780/` or the
actual local port you use; for publication use your HTTPS static-site origin.

## 4. Use it

1. Open Staff workspace and sign in with an approved account.
2. In the **local live application**, inspect an image and ask any evidence questions.
3. Click **Share with staff**. It uploads that saved image, heatmap, measurement
   snapshot and current saved conversation to your private staff workspace.
4. Other approved staff open the static dashboard's Staff workspace to review
   those records and add review notes. Lists refresh every 15 seconds.
5. Staff can archive their own visible shared records. A developer uses the cloud
   recovery view to restore them. Original artifacts remain stored.

Sharing is explicit, not automatic: older private local history is not uploaded
without selecting Share with staff. A shared snapshot is immutable; later local
chat does not silently rewrite the original cloud record. Staff can append notes.

## Local clear history versus cloud history

Local **Clear history** archives all matching local records and preserves their
files/conversations. Local **History recovery** restores them. It does not alter
cloud records. Cloud archiving and recovery use authenticated Supabase RPCs and
developer role checks. Archival is not a backup against project deletion: export
database/storage copies separately under your account's retention policy.

## Live AI and free static hosting

The static site can show samples, benchmark results and authenticated staff data.
It cannot run the Python detector or local Ollama. Live inference still needs a
running backend. Do not expose the current localhost single-user backend publicly
as an authenticated team API; that requires a separately secured deployment.
Supabase stores/authenticates shared records; it does not host this GPU model.

## Required checks after project creation

Test with three separate sessions: anonymous/non-staff must be denied; approved
staff must see shared active records but cannot restore archives; developer must
be able to restore. Verify private image URLs expire, sharing/reported scores
match the local record, archive retains artifacts, and notes cannot impersonate
another author. These hosted checks have not been run without your project.

Official guidance:
https://supabase.com/docs/guides/auth/quickstarts/react
https://supabase.com/docs/guides/database/postgres/row-level-security
https://supabase.com/docs/guides/storage/security/access-control
