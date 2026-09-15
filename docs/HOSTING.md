# Private Fly.io instance

The hosted app is for one trusted learner. The sign-in page uses a standard HTML form over HTTPS (username `learner`), so
password managers can save and fill credentials. Successful sign-in sets a Secure,
HttpOnly, SameSite cookie valid for seven days from sign-in. Sessions survive
server restarts and Fly idle stops; changing the password invalidates them.
The separate CSRF token changes on restart; open tabs refresh it and retry a
rejected write once without replacing the draft. Login cookies are not renewed
automatically. Cookies issued before this restart-persistence fix require one
new sign-in after deployment.
Practice pages and APIs require this cookie; only the login page and its styling
and icon are public. It is not a multi-user
code sandbox: submitted Python can access the instance's practice data and should
only be code you trust. Never share the login or use this as a public code runner.

Local startup remains bound to 127.0.0.1. `--hosted` permits network binding only
when a valid HTTPS origin and a password of at least 24 characters are configured.
Origin, Host and per-session CSRF checks remain enabled in hosted mode.

`fly.toml` uses one 512 MB shared-CPU Machine in Frankfurt. Auto-stop is enabled;
an idle instance may take a moment to start on the next visit. Keep exactly one
Machine: state is a single-user JSON file, not a replicated database.

The persistent volume is mounted at `/data`, with progress in
`/data/practice/progress.json`. The entrypoint initializes its directory and drops
to the unprivileged `learner` account before serving or executing Python. The
container includes only application/exercise files, never local `.judgelab`
progress, credentials, the Git checkout, or a deployment token.

## Deploy from an authenticated workstation

```sh
flyctl apps create judgelab-alonghi --org personal
flyctl volumes create judgelab_data --app judgelab-alonghi --region fra --size 1
# Import JUDGELAB_PASSWORD from a private file or pipe, never a committed file.
flyctl secrets import --app judgelab-alonghi --stage < /path/to/private/runtime.env
flyctl deploy --remote-only --ha=false
```

## Automatic deployment

Every push to `main` runs `.github/workflows/deploy.yml`: Python 3.13 app tests
and Node.js UI tests must pass before Fly.io deploys the pushed commit. Deployments
are serialized and retain `--ha=false` for the single stateful Machine. A manual
rerun is available through GitHub Actions → Deploy to Fly.io → Run workflow on
`main`. Failed tests leave the current deployment running.

The repository's `FLY_API_TOKEN` Actions secret holds a deploy token scoped to
`judgelab-alonghi`, created with a one-year expiry on 2026-09-13. Rotate it before
2027-09-13. The token is provided only to the deploy step, never the runtime app.
To rotate from an authenticated workstation without displaying the token:

```sh
set -o pipefail
flyctl tokens create deploy --app judgelab-alonghi --expiry 8760h \
  --name github-actions-deploy | gh secret set FLY_API_TOKEN --repo ALonghi/judgelab
```

Actions and flyctl are pinned; update their revisions/versions deliberately.
See [Fly.io's GitHub Actions deployment guide](https://fly.io/docs/launch/continuous-deployment-with-github-actions/).

The hosted instance starts with its own progress. Export/import through the app
if you want to move local work; import replaces the target instance's progress.
Fly volume snapshots help recovery, but keep periodic application exports too.

The provided subprocess timeout is not a strict memory/CPU sandbox. Code can
still exhaust the Machine or damage its own data. Authentication limits who can
submit code; it does not change that execution model.
