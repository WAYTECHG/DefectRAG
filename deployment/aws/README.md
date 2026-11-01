# Host the DefectRAG dashboard on AWS (learning project)

**Goal:** a public, read-only dashboard (the saved-example showcase) on AWS, built so you
practise **Budgets, Lightsail, EC2, Lambda and CloudWatch**.
**No GPU, no AI model, no uploads.** The site is plain static files, so it is cheap and safe.

> Prices and Free Plan rules change. Treat every number below as an estimate and check the
> AWS Billing console and the [AWS Pricing Calculator](https://calculator.aws/) before you start.

## What you will build

```
Visitor ──► Lightsail instance (nginx, static IP, firewall)   ← the website  (~$5/month)
              │
              └─ status.html ──► Lambda Function URL (/status)  ← tiny live API
EC2 lab instance (tagged Project=DefectRAG-lab) ← CloudWatch agent, alarms, dashboard
Budgets ──► SNS ──► Lambda "budget guard" ──► stops the EC2 lab instance when spend is high
```

| Skill on your resume | Where you use it here |
|---|---|
| **Budgets** | Phase 1: spending alerts, plus an automatic stop-switch |
| **Lightsail** | Phase 2: the public website |
| **Lambda** | Phase 3: a status API and the budget guard |
| **EC2** | Phase 4: a lab server you start, monitor, then terminate |
| **CloudWatch** | Phase 4: metrics, logs, alarms, one dashboard |

**Rough cost for 178 days:** Lightsail about $30. EC2 lab about $0.40 per day while running, so run it
only while learning. Lambda and CloudWatch basics stay near $0 at this size. Your $199.99 credit is plenty.

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
3. Under **Launch script**, paste the content of [`server/bootstrap.sh`](server/bootstrap.sh).
4. Name it `defectrag-web`. Add tag `Project` = `DefectRAG`. Create.
5. **Networking → Create static IP** and attach it to the instance (free while attached; it is billed if left unattached).
6. **Networking → IPv4 Firewall:** keep **HTTP 80** and **HTTPS 443** open to everyone. Change **SSH 22** to **your own IP only** (add your IP, remove "Any IP").
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

Then on the server (browser SSH):

```bash
sudo certbot --nginx -d your.domain.example --agree-tos -m you@example.com --redirect
sudo certbot renew --dry-run     # proves automatic renewal works
```

### 2.5 Lightsail alarms

Lightsail → your instance → **Metrics**: add alarms for **CPU utilization > 80% for 15 min** and **Status check failed**, with email notification.

## Phase 3: Lambda (60 minutes)

Two small functions are in [`lambda/`](lambda/).

### 3.1 `status_api.py`: a live "status" endpoint

1. Console → **Lambda → Create function** → Author from scratch → name `defectrag-status` → **Python 3.12** → Create.
2. Paste `lambda/status_api.py` into the code editor → **Deploy**.
3. **Configuration → Function URL → Create** → Auth type **NONE** → save. (It only returns harmless public data.)
4. **Configuration → Concurrency** → reserve **5** so a flood of requests cannot run up a bill.
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

## Phase 4: EC2 + CloudWatch lab (90 minutes, then terminate)

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

Take screenshots of: the Budgets page with alerts, the live site URL, the Lambda function with its URL test, the CloudWatch dashboard with an alarm in ALARM, and the Lightsail firewall with SSH limited to your IP. Suggested bullets (edit to match what you really did):

- Deployed a React/Vite analytics dashboard on **Amazon Lightsail** (Ubuntu, nginx, static IP, HTTPS via Let's Encrypt) with SSH restricted by firewall rule.
- Built **AWS Lambda** functions behind a Function URL (status API) and an SNS-triggered cost guard that stops tagged **EC2** instances when **AWS Budgets** thresholds are crossed.
- Configured **CloudWatch** agent metrics, log collection, alarms (CPU, memory, system status with auto-recover) and a dashboard; tested with a load-generated incident.
- Kept the project under a set monthly budget using Budgets alerts, tagging and a documented teardown.

## Phase 6: Teardown (do this before the Free Plan ends)

- [ ] Terminate EC2 instances. Delete unattached **EBS volumes** and **Elastic IPs**.
- [ ] Lightsail: delete the instance, then **release the static IP** (an unattached one is billed).
- [ ] Lambda: delete both functions. SNS: delete the topic.
- [ ] CloudWatch: delete dashboards, alarms, log groups.
- [ ] Budgets: keep one budget until the bill shows $0.00 for a full day.
- [ ] Billing → **Bills** page for the month shows no active charges.

## Troubleshooting

| Problem | Likely fix |
|---|---|
| Site shows nginx welcome page | `deploy_site.sh` did not run, or files are not in `/var/www/defectrag` |
| Blank page after deploy | Run `npm run build:showcase` (not `build`). The normal build expects the Python backend |
| `403` on the site | `sudo chown -R www-data:www-data /var/www/defectrag` |
| Cannot SSH | Your IP changed. Update the firewall rule |
| Budget email never arrives | Confirm the SNS email subscription; billing data can lag several hours |
| Surprise charge | Billing → **Cost Explorer**, group by **Service** and **Usage type** |
