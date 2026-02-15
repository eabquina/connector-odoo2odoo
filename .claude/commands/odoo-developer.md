---
name: odoo-developer
description: >
  Comprehensive Odoo development assistant covering all versions (12–18+). Use this skill whenever the user asks about Odoo module development, Odoo ORM queries, Odoo views/templates, Odoo API integrations, Odoo deployment, Odoo architecture decisions, or any custom Odoo code. Trigger on mentions of: Odoo, OpenERP, odoo.sh, OWL components, QWeb, ir.model.access, __manifest__.py, odoo.conf, XML-RPC/JSON-RPC with Odoo, Odoo wizards, computed fields, onchange, Odoo Docker, Odoo module scaffolding, or any Odoo functional domain (accounting, inventory, manufacturing, CRM, sales, website, HR, purchase, POS, etc.). Also trigger when user mentions extending or inheriting Odoo models/views, or asks about Odoo best practices, even if they don't say "Odoo" explicitly but reference concepts like res.partner, sale.order, or account.move.
---

# Odoo Developer Skill

## First Step: Ask for Odoo Version

**ALWAYS ask which Odoo version the user is targeting before generating any code.** Version differences are significant and affect ORM APIs, view syntax, JS framework (legacy widgets vs OWL), manifest format, and more.

Ask: "Which Odoo version are you working with?"

If the user provides version context in their message or in prior conversation, use that. Otherwise, always ask before proceeding.

## Request Classification

After confirming the version, classify the request into one or more of these areas and read the corresponding reference file(s):

| Area | Reference File | When to Read |
|------|---------------|--------------|
| **Module scaffolding** | `references/module-scaffolding.md` | Creating new modules, manifest files, module structure, security/access rules, menu items |
| **ORM & business logic** | `references/orm-business-logic.md` | Models, fields, computed fields, constraints, wizards, scheduled actions, domain filters |
| **Frontend** | `references/frontend.md` | QWeb templates, XML views, OWL components, JS widgets, website pages, reports |
| **API & integrations** | `references/api-integrations.md` | XML-RPC, JSON-RPC, REST API, external system connectors, webhooks |
| **Solution architecture** | `references/solution-architecture.md` | Multi-module design, data model planning, performance, upgrade strategy |
| **Deployment & DevOps** | `references/deployment.md` | Odoo.sh, Docker, server config, CI/CD, backup, migration |
| **Version differences** | `references/version-differences.md` | When code must differ between versions, breaking changes, migration notes |

Read only the relevant reference file(s) for the current request. For complex requests spanning multiple areas, read multiple files.

## Output Modes

### Full Module Mode
When the user asks to create a module, generate the complete installable file structure:

```
module_name/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── model_name.py
├── views/
│   └── model_name_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── security.xml (if groups needed)
├── data/           (if seed data needed)
├── wizards/        (if transient models needed)
│   ├── __init__.py
│   └── wizard_name.py
├── controllers/    (if HTTP endpoints needed)
│   ├── __init__.py
│   └── main.py
├── static/         (if JS/CSS/images needed)
│   └── src/
│       ├── js/
│       ├── css/ or scss/
│       └── xml/    (QWeb templates for OWL/widgets)
└── reports/        (if PDF reports needed)
    ├── report_templates.xml
    └── report_actions.xml
```

Create each file with proper content. Use `file_create` for each file, then present the full module to the user.

### Snippet Mode
When the user asks a specific question or needs a focused code sample, provide well-commented code snippets with:
- Version-specific syntax noted in comments
- Import statements included
- Context on where the snippet goes in the module structure

## Code Style Conventions

Follow OCA (Odoo Community Association) coding standards:
- PEP 8 for Python, with Odoo-specific conventions
- Model names: `dot.separated.lowercase` (e.g., `sale.order.line`)
- Python class names: CamelCase (e.g., `SaleOrderLine`)
- XML IDs: `module_name.snake_case_id` (e.g., `my_module.view_partner_form_inherit`)
- Field names: `snake_case`
- Method names: `snake_case`, prefixed by purpose (`_compute_`, `_onchange_`, `_check_`, `_prepare_`, `action_`)
- Security groups: `module_name.group_descriptive_name`
- Data files listed in `__manifest__.py` `data` key in dependency order
- Demo data in `demo` key, never in `data`

### Module Naming Convention

Apply these naming rules when generating module names:

**Inheriting/extending an existing Odoo module:**
```
<parent_module>_<customer_name>
```
Examples:
- `sale_acme` — Sale customizations for Acme Corp
- `account_globex` — Accounting customizations for Globex
- `purchase_initech` — Purchase customizations for Initech
- `sale_subscription_acme` — Sale Subscription customizations for Acme

**Entirely new module (not inheriting a standard module):**
```
<customer_name>_<module_name>
```
Examples:
- `acme_approval_workflow` — Custom approval workflow for Acme
- `globex_asset_tracking` — New asset tracking module for Globex

**Ask the user for the customer name** if not provided, so the module can be named correctly.

## Common Patterns to Know

When generating code, apply these patterns automatically:

1. **Inheritance**: Use `_inherit` for extending, `_inherits` for delegation. Always set `_name` only when creating new models.
2. **Security first**: Always generate `ir.model.access.csv` entries. Remind user about record rules if multi-company.
3. **Translations**: Use `_()` for user-facing strings in Python. Mark XML strings with `t-translate` where needed.
4. **API decorators**: Use correct decorators for the version (`@api.multi`/`@api.one` removed in 13+, `@api.depends`, `@api.constrains`, `@api.onchange`).
5. **Upgrade safety**: For inherited models, always use `comodel_name` as kwarg, always handle `False`/empty recordsets.

## Workflow Summary

1. **Ask Odoo version** (if not known)
2. **Classify the request** → read relevant reference file(s)
3. **Generate code** in the appropriate output mode (full module or snippet)
4. **Include version-specific notes** if the syntax differs across versions
5. **Add security, translations, and tests** reminders where appropriate
