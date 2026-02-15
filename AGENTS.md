# connector-odoo2odoo - Agent Notes (Odoo 18)

## Scope & Stack
- Target Odoo: **18.0** (this code runs in the target instance).
- Source Odoo: often older versions (e.g., **13.0**) via RPC through `connector` / `connector_odoo`.
- Architecture: OCA `component` framework + `connector` mappers/adapters + `queue_job` for async imports/exports.

## Connector Architecture (patterns to follow)
- **Binding models**: `odoo.<model>` inherit `odoo.binding` and delegate to the core model via `_inherits` (pointer field usually `odoo_id`).
- **Components** (per model):
  - Adapter: `_inherit = "odoo.adapter"` and `_odoo_model = "<remote.model>"`.
  - Mapper: `_inherit = "odoo.import.mapper"` / `"odoo.export.mapper"`; keep direct mappings in `direct = [...]`.
  - Importer/Exporter: `_inherit = "odoo.importer"` / `"odoo.exporter"`; use `_before_import()` for defaults and dependency resolution.
  - Listener: `_inherit = "base.connector.listener"` for outbound sync triggers (when enabled).
- **Id strategy**: `external_id` is the *remote* database record id; always consider backend scoping (multiple backends) when adding constraints/searches.

## Odoo 18 / Cross-Version Gotchas (source Odoo 13+)
- Never assume fields exist across versions; guard mappings with `if "<field>" in self.env["<model>"]._fields:` (or check `record._fields`) and return `{}` when absent.
- `account.account`:
  - Odoo 13: uses `user_type_id` (m2o to `account.account.type`).
  - Odoo 14+ (incl. 17/18): uses `account_type` (selection); `user_type_id` is removed.
- Views (Odoo 17+): XML `attrs=` and `states=` are invalid; migrate to the supported modifier syntax for your target Odoo version.

## Core Models We Commonly Sync (non-exhaustive)
- Base: `res.partner`, `res.company`, `res.users`, `res.currency`, `ir.model.data`
- Product: `product.template`, `product.product`, `product.category`, `uom.uom`
- Sales/Purchase: `sale.order`, `sale.order.line`, `purchase.order`, `purchase.order.line`
- Stock: `stock.picking`, `stock.move`, `stock.move.line`, `stock.location`, `stock.warehouse`, `stock.lot`
- Accounting: `account.account`, `account.journal`, `account.tax`, `account.move`, `account.move.line`, `account.payment`
- HR: `hr.employee`, `hr.department`, `hr.job`, `hr.contract`, `hr.leave`, `hr.attendance`

## Workflow
- Prefer minimal, model-scoped changes; keep import logic in the model’s `importer.py` and mappings in the mapper class.
- When fixing a sync issue, reproduce by running a single import job and inspecting:
  - mapped values (`map_record.values(...)`)
  - created/linked local record (`odoo_id`)
  - binder resolution for dependencies
- Run repo checks on touched files when practical: `pre-commit run --files <files...>`.

## Version Control
- For every change, create a git commit with a clear message and push it to the remote branch (unless explicitly told not to).
