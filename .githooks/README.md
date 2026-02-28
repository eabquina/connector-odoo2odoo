# Repository Git Hooks

Enable tracked hooks in this repository:

```bash
git config core.hooksPath .githooks
```

Configure the deploy webhook URL locally (not committed to git):

```bash
git config connector-odoo.deploywebhookurl "https://your-webhook-url"
```

With this setting, `.githooks/post-commit` sends a `POST` request on every
local commit.
