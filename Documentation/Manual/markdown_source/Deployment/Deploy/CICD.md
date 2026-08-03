# CI/CD — Push-to-Deploy (GitHub Actions → FTPS)

**In a phrase:** push a branch → GitHub Actions builds the manifest and
FTPS-uploads only what changed; the branch name picks the environment.

There is **no app server and no bundler**. `FrontEnd/` is a static site that
transpiles JSX in-browser (CDN React + Babel), so the pipeline needs only
Python — no Node/npm.

## Branch = environment

| Push / PR to        | Workflow                              | GitHub Environment |
|---------------------|---------------------------------------|--------------------|
| `sandbox`, `develop`| `.github/workflows/deploy-sandbox.yml`| `sandbox`          |
| `main`              | `.github/workflows/deploy-production.yml` | `production`   |

- **Push** → deploys. **Pull request** → validates only (compiles the deploy
  script), never uploads.
- **Promotion is a fast-forward, not a rebuild:**
  `git push origin sandbox:main` moves prod to the exact commit already
  validated in sandbox.

## What each run does

1. `actions/checkout` with **`fetch-depth: 0`** — full history, because the
   deploy diffs `github.event.before..github.sha` to decide what to upload.
2. `setup-python@3.11` + `pip install -r FrontEnd/requirements-deploy.txt`
   (`paho-mqtt` for the build stamp).
3. Runs `python3 FrontEnd/deploy_FTP_to_like_dot_audio.py`, which:
   - regenerates `FrontEnd/api/tree.json` from `Gui_Frames`,
   - best-effort refreshes `FrontEnd/api/grabbag` (skipped in CI — no local
     backend; the committed copy ships instead),
   - connects over **explicit FTPS** (falls back to plain FTP unless
     `DEPLOY_FTP_REQUIRE_TLS=1`),
   - uploads only the FrontEnd files changed in the push range, **always**
     re-uploading `api/tree.json`, `api/grabbag`, and `index.html`, with
     **`index.html` last** for a near-atomic cutover,
   - publishes a build stamp (commit + timestamp + env) to MQTT for
     observability.

## Required secrets (per GitHub Environment)

Set these under **Settings → Environments → `sandbox`** and **`production`**
(same names, different values — that is what separates the two environments):

| Secret        | Required | Notes                                   |
|---------------|----------|-----------------------------------------|
| `FTP_HOST`    | yes      | FTPS host                               |
| `FTP_USER`    | yes      |                                         |
| `FTP_PASS`    | yes      |                                         |
| `REMOTE_DIR`  | yes      | remote docroot, e.g. `/`                |
| `MQTT_HOST`   | no       | omit to skip the build stamp            |
| `MQTT_PORT`   | no       | default `1883`                          |
| `MQTT_USER`   | no       |                                         |
| `MQTT_PASS`   | no       |                                         |
| `MQTT_TOPIC`  | no       | default `OpenAir/Deploy/stamp`          |

**GitHub Environments are the store of record for every secret.** Nothing is
committed, and the repository holds no credential of its own. The optional local
gitignored **repo-root `.env`** exists only to seed those secrets when running
this script by hand.

> This section used to name `FrontEnd/.env`. That path no longer exists and must
> not be re-created — it is where an executive review found a plaintext
> production credential. Both deploy workflows exclude `**/.env` and `**/.env.*`
> from upload; keep it that way.

## deploy.py env-var switches

The same script serves the laptop and CI. Behavior is env-driven:

| Env var                  | Effect                                                        |
|--------------------------|--------------------------------------------------------------|
| `DEPLOY_DIFF_BASE`/`_HEAD` | commit-range mode (upload only files changed in the range) |
| `DEPLOY_FULL_SYNC=1`     | force full mtime/size sync of every file                     |
| `DEPLOY_FTP_PLAIN=1`     | skip FTPS, use plain FTP                                      |
| `DEPLOY_FTP_REQUIRE_TLS=1` | abort instead of falling back to plain FTP                 |
| `DEPLOY_ENV`             | label used in the MQTT build stamp                           |
| *(none set)*             | local mode: upload uncommitted working-tree changes          |

- A **null/first-push** base (`000000…`) or `DEPLOY_FULL_SYNC=1` → full sync.
- To force a complete re-sync from CI, run the workflow with
  `DEPLOY_FULL_SYNC=1`, or push after setting it.

## First-time setup checklist

1. Create the `sandbox` and `production` Environments in GitHub with the
   secrets above.
2. Create a `sandbox` branch: `git switch -c sandbox && git push -u origin sandbox`.
3. Confirm the host accepts **explicit FTPS**. If not, add
   `DEPLOY_FTP_PLAIN=1` to the workflow `env:` (transport stays unencrypted —
   creds remain safe in GitHub secrets).
4. First deploy runs a full sync (no previous ref); subsequent pushes are
   incremental.
