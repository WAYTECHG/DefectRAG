# Host the DefectRAG dashboard on AWS (learning project)

**Goal:** a public, read-only dashboard (the saved-example showcase) on AWS, built so you
practise **Budgets, Lightsail, Lambda, SNS, IAM and CloudWatch**. An EC2 lab server (Phase 4) is an optional extra.
**No GPU, no AI model, no uploads.** The site is plain static files, so it is cheap and safe.
Live inspection runs on the Hugging Face Space; this site only shows saved results.

**Status (9 Nov 2026):** Phases 1, 2, 3 and the monitoring part of 5 are built and live (HTTPS site, status API,
budget guard, CloudWatch alarm and dashboard, Lightsail alarms). Phase 4 (EC2 lab) was skipped on purpose.

> Prices and Free Plan rules change. Treat every number below as an estimate and check the
> AWS Billing console and the [AWS Pricing Calculator](https://calculator.aws/) before you start.

## What you will build

```
Visitor ──► Lightsail instance (nginx, static IP, firewall, Let's Encrypt HTTPS)   ← the website  (~$5/month)
              │
              └─ status.html ──► Lambda Function URL (/status)  ← tiny live API
                                      │
                                      └─ CloudWatch: dashboard + error alarm ──► SNS topic ──► email
Lightsail alarms (status check, CPU, burst capacity) ──► email
Budgets ──► SNS ──► Lambda "budget guard"  (stops tagged EC2 lab instances; none exist unless you do Phase 4)
```

| Skill on your resume | Where you use it here                                              |
| -------------------- | ------------------------------------------------------------------ |
| **Budgets**    | Phase 1: spending alerts, plus an automatic stop-switch            |
| **Lightsail**  | Phase 2: the public website with HTTPS and instance alarms         |
| **Lambda**     | Phase 3: a status API and the budget guard                         |
| **SNS / IAM**  | Phase 3: alert topics, one least-privilege role per function       |
| **CloudWatch** | Phase 4: Lambda dashboard and an error alarm that emails you       |
| **EC2**        | Phase 4b (optional, not done here): a lab server with the agent    |

**Rough cost for 178 days:** Lightsail about $30. Lambda, SNS and CloudWatch basics stay near $0 at this size.
An optional EC2 lab costs about $0.40 per day while running, so run it only while learning.

## Rules that protect your credit (do these first)

1. **Phase 1 (Budgets) before anything else.**
2. **Never use the root account for daily work.** Turn on MFA for root, then create an admin IAM user (or IAM Identity Center user) with MFA and use that.
3. **Do not create access keys for root.** Do not put keys in the website or in Git.
4. **One AWS Region for everything** (for example `us-east-1` or the one closest to you). Resources in other regions are easy to forget.
5. **Tag every resource** `Project=DefectRAG`. Tags make cleanup easy.
6. **Free Plan end date:** the plan ends after 6 months or when credits run out, whichever comes first, and the account can close unless you upgrade. Put a calendar reminder at **day 150** to decide: upgrade, or run the teardown in Phase 6 and keep screenshots for your portfolio.

## Phase 1: Budgets (20 minutes)

1. Console → **Billing and Cost Management → Budgets → Create budget**.
2. Choose **Customize → Cost budget**. Name `defectrag-monthly`. Period **Monthly**. Amount **$20**.
3. Add three alerts on **Actual** cost: **50%**, **80%**, **100%**. Send to your email.
4. Add one alert on **Forecasted** cost at **100%**.
5. Also open **Billing → Credits** and note the balance and expiry. Check it every Sunday.
6. **Optional stop-switch (Phase 3):** make the 100% alert publish to an **SNS topic** so Lambda can stop the lab server.

> Budgets data is delayed by several hours. Alerts are a safety net, not a real-time limit. Terminating things you do not use is the real protection.

## Phase 2: Lightsail website (45 minutes)

### 2.1 Build the site on your PC

```bash
cd frontend
npm ci
npm run build:showcase      # creates frontend/dist-static
```

Test it locally first: `python -m http.server 8771 --directory frontend/dist-static`, then open http://127.0.0.1:8771.

### 2.2 Create the server

1. Console → **Lightsail → Create instance**. Linux/Unix, **OS only → Ubuntu 24.04 LTS**.
2. Plan: the **$5/month** plan with a public IPv4 address (check that it includes IPv4).
3. Under **Launch script**, paste the content of [`server/bootstrap.sh`](server/bootstrap.sh). Include the first line, `#!/bin/bash`. Without it the script runs under `sh`, fails at `set -o pipefail` and nginx is never installed (see Troubleshooting).
4. Name it `defectrag-web`. Add tag `Project` = `DefectRAG`. Create.
5. **Networking → Create static IP** and attach it to the instance (free while attached; it is billed if left unattached).
6. **Networking → IPv4 Firewall:** keep **HTTP 80** open and add **HTTPS 443**, both to everyone. Change **SSH 22** to **your own IP only** (add your IP, remove "Any IP"). Some internet providers rotate your public address between blocks (check `https://checkip.amazonaws.com` a few times). If it changes, allow the whole `/24` block of each address you see, not a single `/32`. Keep the **Lightsail browser SSH** tick, which works without your IP.
7. Download the default SSH key from **Account → SSH keys**, or use the browser SSH button.

### 2.3 Publish

```bash
export WEB_HOST=<your static IP>
export WEB_KEY=~/Downloads/LightsailDefaultKey.pem
bash deployment/aws/deploy_site.sh
```

Open `http://<static IP>`. You should see the same dashboard as the local preview.

### 2.4 HTTPS (recommended)

You need a **domain name** pointing at the static IP.

- Cheap: register a domain in **Route 53** (check the price first; domain fees may not be covered by credits) or use any registrar.
- Free option: a free dynamic-DNS subdomain such as DuckDNS pointing at the static IP.

Then **on the server** (browser SSH, not your own computer). First tell nginx its name, because certbot looks for a matching `server_name`:

```bash
sudo sed -i 's/server_name _;/server_name your.domain.example;/' /etc/nginx/sites-available/defectrag
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your.domain.example --agree-tos -m you@example.com --no-eff-email --redirect
sudo certbot renew --dry-run     # proves automatic renewal works
```

### 2.5 Lightsail alarms

Lightsail → your instance → **Metrics**: add alarms for **Status check failed** (rule **greater than or equal to 1**; the metric is 0 or 1, so "greater than 1" never fires), **CPU utilization > 80% for 15 min**, and **Burst capacity percentage < 10%** (a $5 plan is burstable and is throttled when the capacity reaches 0). Tick **Email**. Lightsail alarms are Lightsail's own, not CloudWatch alarms.

## Phase 3: Lambda (60 minutes)

Two small functions are in [`lambda/`](lambda/).

### 3.1 `status_api.py`: a live "status" endpoint

1. Console → **Lambda → Create function** → Author from scratch → name `defectrag-status` → **Python 3.12** → Create.
2. Paste `lambda/status_api.py` into the code editor, and set **Runtime settings → Handler** to `lambda_function.handler` (the console names the file `lambda_function.py`) → **Deploy**. Update `SAVED_EXAMPLES` when the showcase size changes (now 24).
3. **Configuration → Function URL → Create** → Auth type **NONE** → save. (It only returns harmless public data.)
4. **Configuration → Concurrency** → reserve **5** so a flood of requests cannot run up a bill. New accounts often cannot (the total limit is 10 and AWS keeps 100 unreserved), so skip it there; the function is tiny, returns harmless data, and the Budgets alert is the safety net.
5. Test: `curl <function-url>` should return JSON.
6. Put the URL in the site: `export STATUS_URL=<function-url>` and run `deploy_site.sh` again. Open `http://<ip>/status.html`.

### 3.2 `budget_guard.py`: the stop-switch

1. Console → **SNS → Topics → Create topic** (Standard) `defectrag-budget-alerts`.
2. In the topic's **Access policy**, allow `budgets.amazonaws.com` to publish (AWS Budgets console shows the exact policy when you add an SNS target).
3. Create Lambda `defectrag-budget-guard` (Python 3.12), paste `lambda/budget_guard.py`.
4. **Configuration → Permissions →** edit the execution role, attach [`lambda/budget_guard_policy.json`](lambda/budget_guard_policy.json) as an inline policy.
5. **Add trigger → SNS →** `defectrag-budget-alerts`.
6. Edit the `defectrag-monthly` budget → 100% alert → add the SNS topic.
7. **Test safely:** in Lambda, run the test event `{"dry_run": true}`. It lists what *would* be stopped and stops nothing.

The guard only stops EC2 instances tagged `Project=DefectRAG-lab`. It cannot touch Lightsail or anything else.

## Phase 4: CloudWatch monitoring (30 minutes)

Built and live. It watches the real Lambda functions, so no EC2 server is needed.

1. **SNS → Topics → Create topic** (Standard) `defectrag-alerts`, tag `Project=DefectRAG`. Add an **Email** subscription and click **Confirm** in the message you receive. Do **not** reuse `defectrag-budget-alerts`: the budget guard Lambda is subscribed to it, so an alarm posted there would trigger the guard.
2. **CloudWatch → Alarms → Create alarm** → metric **Lambda → By Function Name → `defectrag-status` → Errors**. Statistic **Sum**, period **5 minutes**, **Greater/Equal 1**, missing data **treated as good** (the function rarely runs). Action: notify `defectrag-alerts`. Name `defectrag-status-errors`.
3. **CloudWatch → Dashboards → Create** `defectrag`. Add: a line widget for `defectrag-status` Invocations and Errors, a second for Duration (milliseconds, so it needs its own axis), an **Alarm status** widget for `defectrag-status-errors`, and a widget for `defectrag-budget-guard` Invocations/Errors (empty until a budget alert fires, which is expected). **Click Save dashboard**; unsaved widgets disappear.
4. Open `status.html` a few times so the graphs have data points. The alarm starts as "Insufficient data" and turns **OK** after a few minutes.

## Phase 4b (optional, not done here): EC2 lab with the CloudWatch agent (90 minutes, then terminate)

1. **EC2 → Launch instance.** Name `defectrag-lab`. Amazon Linux 2023. Type `t3.micro` (or the type the Free Plan offers). Tag `Project=DefectRAG-lab`.
2. Security group: SSH from **your IP only**, HTTP 80 from anywhere.
3. Advanced → **IAM instance profile**: create a role with the managed policy `CloudWatchAgentServerPolicy` and attach it.
4. Connect (EC2 Instance Connect), then:

```bash
sudo dnf install -y nginx amazon-cloudwatch-agent
sudo systemctl enable --now nginx
```

5. Put the config from [`cloudwatch/agent-config.json`](cloudwatch/agent-config.json) at
   `/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`, then:

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

6. **CloudWatch → Alarms → Create alarm:**
   - `CPUUtilization` ≥ 70% for 2 of 3 five-minute periods → email via SNS.
   - `StatusCheckFailed_System` ≥ 1 → action **Recover this instance**.
   - `mem_used_percent` (from the agent) ≥ 85% → email.
7. **CloudWatch → Dashboards → Create** `defectrag`: CPU, memory, disk, network, and a Logs Insights widget for nginx 5xx errors.
8. **Practice an incident:** run `sudo dnf install -y stress-ng && stress-ng --cpu 2 --timeout 600s`, watch the alarm go from OK → ALARM and read the email. Write down what you saw.
9. **Terminate the instance** when finished (Instances → Instance state → Terminate). Check log retention is **7 days** (Logs → Log groups → Actions → Edit retention).

## Phase 5: Evidence for your resume

Take screenshots of: the Budgets page with alerts, the live site on HTTPS (padlock), the Lambda function with its URL test, the CloudWatch dashboard with the alarm showing OK, and the Lightsail firewall with SSH limited to your IP ranges (hide the addresses if you publish it). Suggested bullets (edit to match what you really did):

- Hosted a React/Vite showcase on **Amazon Lightsail** (Ubuntu, nginx, static IP, HTTPS via Let's Encrypt) with SSH restricted by firewall rule and repeatable deployment through a shell script.
- Built **AWS Lambda** functions behind a Function URL (status API) and an SNS-triggered cost guard, each with its own least-privilege **IAM** role, plus **AWS Budgets** alerts.
- Monitored the stack with a **CloudWatch** dashboard and an error alarm that emails through **SNS**, and with Lightsail alarms for status check, CPU and burst capacity.
- Kept the project under a set monthly budget using Budgets alerts, tagging and a documented teardown.

## Phase 6: Teardown (do this before the Free Plan ends)

- [ ] If you did Phase 4b: terminate EC2 instances. Delete unattached **EBS volumes** and **Elastic IPs**.
- [ ] Lightsail: delete the instance's alarms with it, and delete the DuckDNS name if you no longer need it.
- [ ] Lightsail: delete the instance, then **release the static IP** (an unattached one is billed).
- [ ] Lambda: delete both functions. SNS: delete the topic.
- [ ] CloudWatch: delete dashboards, alarms, log groups.
- [ ] Budgets: keep one budget until the bill shows $0.00 for a full day.
- [ ] Billing → **Bills** page for the month shows no active charges.

## Troubleshooting

| Problem                       | Likely fix                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------- |
| Site shows nginx welcome page | `deploy_site.sh` did not run, or files are not in `/var/www/defectrag`                  |
| Blank page after deploy       | Run `npm run build:showcase` (not `build`). The normal build expects the Python backend |
| `403` on the site           | `sudo chown -R www-data:www-data /var/www/defectrag`                                      |
| Cannot SSH (timeout)          | Your IP changed. Some providers rotate between two blocks; allow the `/24` of each, see 2.2 |
| nginx missing after first boot | Launch script ran under `sh` (`set: Illegal option -o pipefail` in `/var/log/cloud-init-output.log`). Re-run it with `sudo bash` |
| `sudo: disabled` / `command not found` | You ran the command on your own PC. Run it on the server (prompt `ubuntu@ip-...`)   |
| `mktemp ... Permission denied` in deploy | Old script version; use the current `deploy_site.sh` (it uses `sudo` for `/var/www`)  |
| `tar: file changed as we read it` | Old script version wrote the archive inside the folder it was packing; use the current one |
| Status alarm "Insufficient data" | Normal for a function that rarely runs; set missing data to "good" and wait a few minutes |
| Budget email never arrives    | Confirm the SNS email subscription; billing data can lag several hours                      |
| Surprise charge               | Billing → **Cost Explorer**, group by **Service** and **Usage type**     |
