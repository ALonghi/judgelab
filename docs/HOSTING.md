# Private Fly.io instance

The hosted app is for one trusted learner. Every page, asset and API route requires
HTTP Basic authentication over HTTPS (username `learner`). It is not a multi-user
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

No GitHub deployment secret is needed for a direct CLI deployment. If CI is added
later, use an app-scoped, expiring Fly deploy token in a GitHub Actions secret.
Do not put a Fly deployment token in the application's runtime environment.

The hosted instance starts with its own progress. Export/import through the app
if you want to move local work; import replaces the target instance's progress.
Fly volume snapshots help recovery, but keep periodic application exports too.

The provided subprocess timeout is not a strict memory/CPU sandbox. Code can
still exhaust the Machine or damage its own data. Authentication limits who can
submit code; it does not change that execution model.
