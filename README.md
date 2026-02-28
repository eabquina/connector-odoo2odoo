
[![Runboat](https://img.shields.io/badge/runboat-Try%20me-875A7B.png)](https://runboat.odoo-community.org/builds?repo=OCA/connector-odoo2odoo&target_branch=17.0)
[![Pre-commit Status](https://github.com/OCA/connector-odoo2odoo/actions/workflows/pre-commit.yml/badge.svg?branch=17.0)](https://github.com/OCA/connector-odoo2odoo/actions/workflows/pre-commit.yml?query=branch%3A17.0)
[![Build Status](https://github.com/OCA/connector-odoo2odoo/actions/workflows/test.yml/badge.svg?branch=17.0)](https://github.com/OCA/connector-odoo2odoo/actions/workflows/test.yml?query=branch%3A17.0)
[![codecov](https://codecov.io/gh/OCA/connector-odoo2odoo/branch/17.0/graph/badge.svg)](https://codecov.io/gh/OCA/connector-odoo2odoo)
[![Translation Status](https://translation.odoo-community.org/widgets/connector-odoo2odoo-17-0/-/svg-badge.svg)](https://translation.odoo-community.org/engage/connector-odoo2odoo-17-0/?utm_source=widget)

<!-- /!\ do not modify above this line -->

# connector-odoo2odoo

TODO: add repo description.

## Local Auto Deploy Webhook

Run these commands once in your local clone:

```bash
git config core.hooksPath .githooks
git config connector-odoo.deploywebhookurl "https://your-webhook-url"
```

When `connector-odoo.deploywebhookurl` is configured, each local `git commit`
triggers a POST request from `.githooks/post-commit`.

## GitHub Actions Auto Deploy Webhook

The repository includes `.github/workflows/deploy-webhook.yml` which triggers on
push to `18.0` and posts to a webhook URL from a GitHub secret.

Set this repository secret in GitHub:

- Name: `ODOO_DEPLOY_WEBHOOK_URL`
- Value: your full deploy webhook URL

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

This part will be replaced when running the oca-gen-addons-table script from OCA/maintainer-tools.

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Odoo Community Association (OCA)
policy. Consult each module's `__manifest__.py` file, which contains a `license` key
that explains its license.

----
OCA, or the [Odoo Community Association](http://odoo-community.org/), is a nonprofit
organization whose mission is to support the collaborative development of Odoo features
and promote its widespread use.
