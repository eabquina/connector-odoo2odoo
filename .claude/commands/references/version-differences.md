# Version Differences Reference

## Quick Version Compatibility Table

| Feature | Odoo 12 | Odoo 13 | Odoo 14 | Odoo 15 | Odoo 16 | Odoo 17 | Odoo 18 |
|---------|---------|---------|---------|---------|---------|---------|---------|
| `@api.multi` | Required | Removed | - | - | - | - | - |
| `@api.one` | Required | Removed | - | - | - | - | - |
| `@api.model_create_multi` | Added | Default | - | - | - | - | - |
| Assets (manifest) | XML | XML | Python | Python | Python | Python | Python |
| OWL Version | - | - | OWL 1 | OWL 1 | OWL 2 | OWL 2 | OWL 2 |
| View `attrs` | Supported | Supported | Supported | Supported | Supported | Deprecated | Removed |
| View `states` | Supported | Supported | Supported | Supported | Supported | Deprecated | Removed |
| `env.user.company_id` | Required | Deprecated | - | - | - | - | - |
| `env.company` | - | Added | Default | Default | Default | Default | Default |
| Python | 3.5+ | 3.6+ | 3.6+ | 3.8+ | 3.8+ | 3.10+ | 3.10+ |
| PostgreSQL | 9.5+ | 10+ | 10+ | 12+ | 12+ | 12+ | 14+ |

## API Decorator Changes

### Odoo 12 and below

```python
from odoo import api, models


class MyModel(models.Model):
    _name = "my.model"

    @api.multi
    def action_process(self):
        """Process multiple records."""
        for record in self:
            record.state = "done"
        return True

    @api.one
    def action_single(self):
        """Process single record (returns list)."""
        self.state = "done"
        return True

    @api.model
    def create(self, vals):
        """Create single record."""
        return super(MyModel, self).create(vals)
```

### Odoo 13+

```python
from odoo import api, models


class MyModel(models.Model):
    _name = "my.model"

    # @api.multi is now default - removed
    def action_process(self):
        """Process records (self is always recordset)."""
        for record in self:
            record.state = "done"
        return True

    # @api.one removed - always iterate manually
    def action_single(self):
        """Process each record."""
        for record in self:
            record.state = "done"
        return True

    @api.model_create_multi  # New in 12, default behavior in 13+
    def create(self, vals_list):
        """Create multiple records at once."""
        return super().create(vals_list)
```

## View Syntax Changes

### Odoo 16 and below (attrs/states)

```xml
<!-- Using attrs (deprecated in 17) -->
<field name="discount"
       attrs="{'invisible': [('state', '!=', 'draft')],
               'readonly': [('state', '=', 'done')],
               'required': [('type', '=', 'service')]}"/>

<!-- Using states (deprecated in 17) -->
<button name="action_confirm" string="Confirm"
        states="draft,sent"/>

<button name="action_cancel" string="Cancel"
        attrs="{'invisible': [('state', 'in', ['done', 'cancel'])]}"/>
```

### Odoo 17+ (inline modifiers)

```xml
<!-- Direct boolean expressions -->
<field name="discount"
       invisible="state != 'draft'"
       readonly="state == 'done'"
       required="type == 'service'"/>

<!-- Button visibility -->
<button name="action_confirm" string="Confirm"
        invisible="state not in ('draft', 'sent')"/>

<button name="action_cancel" string="Cancel"
        invisible="state in ('done', 'cancel')"/>

<!-- Complex conditions -->
<field name="tax_id"
       invisible="not company_id or state == 'done'"
       required="type == 'product' and state == 'draft'"/>

<!-- Column invisibility in tree -->
<tree>
    <field name="partner_id"/>
    <field name="discount" column_invisible="parent.state == 'done'"/>
</tree>
```

## Company Access Changes

### Odoo 12 and below

```python
# Get current company
company = self.env.user.company_id

# Get allowed companies
companies = self.env.user.company_ids

# Change company context
self.with_context(force_company=company.id)
```

### Odoo 13+

```python
# Get current company
company = self.env.company

# Get allowed companies
companies = self.env.companies

# Company IDs for domains
company_ids = self.env.context.get("allowed_company_ids", [self.env.company.id])

# Change company
self.with_company(company)

# Multi-company record rules use company_ids
# domain_force = [('company_id', 'in', company_ids)]
```

## Asset Management

### Odoo 13 and below (XML)

```xml
<!-- In views/assets.xml -->
<template id="assets_backend" inherit_id="web.assets_backend">
    <xpath expr="." position="inside">
        <script type="text/javascript"
                src="/my_module/static/src/js/widget.js"/>
        <link rel="stylesheet" type="text/css"
              href="/my_module/static/src/css/style.css"/>
    </xpath>
</template>
```

### Odoo 14+ (Manifest)

```python
# In __manifest__.py
{
    "assets": {
        "web.assets_backend": [
            "my_module/static/src/js/**/*.js",
            "my_module/static/src/css/**/*.css",
            "my_module/static/src/xml/**/*.xml",
            # Exclude specific files
            ("remove", "my_module/static/src/js/old_widget.js"),
            # Prepend (load first)
            ("prepend", "my_module/static/src/js/priority.js"),
            # After specific file
            ("after", "web/static/src/js/some_file.js",
             "my_module/static/src/js/depends_on_some_file.js"),
        ],
        "web.assets_frontend": [
            "my_module/static/src/js/public.js",
        ],
        "web.report_assets_common": [
            "my_module/static/src/css/report.css",
        ],
    },
}
```

## Account Module Changes

### account.account.type (Odoo 12-13)

```python
# Odoo 12-13: account.account.type model exists
class AccountAccount(models.Model):
    _inherit = "account.account"

    user_type_id = fields.Many2one(
        comodel_name="account.account.type",
        string="Type",
    )

# To get account type:
account_type = account.user_type_id.type  # 'receivable', 'payable', etc.
```

### account_type Selection (Odoo 14+)

```python
# Odoo 14+: account_type is selection field
class AccountAccount(models.Model):
    _inherit = "account.account"

    # Built-in selection field
    account_type = fields.Selection(
        selection=[
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("expense", "Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),
            ("off_balance", "Off-Balance Sheet"),
        ],
    )
```

### Cross-Version Compatibility

```python
class AccountAccountMapper(Component):
    _inherit = "odoo.import.mapper"

    @mapping
    def account_type_mapping(self, record):
        """Handle account type across versions."""
        # Check target Odoo version
        if "account_type" in self.env["account.account"]._fields:
            # Odoo 14+: use selection
            type_map = {
                "receivable": "asset_receivable",
                "payable": "liability_payable",
                "liquidity": "asset_cash",
                "other": "asset_current",
            }
            return {"account_type": type_map.get(record.get("type"), "asset_current")}
        else:
            # Odoo 12-13: use Many2one
            account_type = self.env["account.account.type"].search([
                ("type", "=", record.get("type")),
            ], limit=1)
            return {"user_type_id": account_type.id if account_type else False}
```

## OWL Component Changes

### Odoo 14-15 (OWL 1)

```javascript
odoo.define("my_module.MyComponent", function (require) {
    "use strict";

    const { Component } = owl;
    const { useState } = owl.hooks;
    const AbstractAction = require("web.AbstractAction");
    const core = require("web.core");

    class MyComponent extends Component {
        constructor() {
            super(...arguments);
            this.state = useState({ count: 0 });
        }

        increment() {
            this.state.count++;
        }
    }

    MyComponent.template = "my_module.MyComponent";

    core.action_registry.add("my_action", MyComponent);

    return MyComponent;
});
```

### Odoo 16+ (OWL 2)

```javascript
/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MyComponent extends Component {
    static template = "my_module.MyComponent";
    static props = {
        recordId: { type: Number, optional: true },
    };

    setup() {
        this.state = useState({ count: 0 });
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    increment() {
        this.state.count++;
    }

    async loadData() {
        const data = await this.orm.searchRead("res.partner", [], ["name"]);
        console.log(data);
    }
}

registry.category("actions").add("my_action", MyComponent);
```

## Python Version Requirements

### Syntax Differences

```python
# Python 3.8+ (Odoo 15+): Walrus operator
if (match := pattern.search(text)):
    process(match.group())

# Python 3.10+ (Odoo 17+): Structural pattern matching
match command:
    case "start":
        start_process()
    case "stop":
        stop_process()
    case _:
        unknown_command()

# Python 3.10+: Union types
def process(value: int | str | None) -> dict[str, Any]:
    pass

# Earlier versions
from typing import Union, Dict, Any, Optional
def process(value: Union[int, str, None]) -> Dict[str, Any]:
    pass
```

## Field Changes

### Website Module (Odoo 16+)

```python
# Odoo 15 and below
is_published = fields.Boolean(string="Published")

# Odoo 16+: website.published.mixin
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["website.published.mixin"]

    # is_published comes from mixin
    # website_url computed field available
```

### Mail Tracking (Odoo 13+)

```python
# Odoo 12: track_visibility
name = fields.Char(track_visibility="onchange")
state = fields.Selection(track_visibility="always")

# Odoo 13+: tracking
name = fields.Char(tracking=True)
state = fields.Selection(tracking=True)
```

## Migration Helpers

### Version Detection

```python
from odoo.tools import version


def get_odoo_major_version():
    """Get major Odoo version as integer."""
    return int(version.version.split(".")[0])


# In code
if get_odoo_major_version() >= 17:
    # Use new syntax
    pass
else:
    # Use legacy syntax
    pass
```

### Field Existence Check

```python
def safe_mapping(self, record):
    """Safely map fields that may not exist."""
    values = {}

    # Check if field exists in target model
    model = self.env["account.account"]

    if "account_type" in model._fields:
        values["account_type"] = self._map_account_type(record)
    elif "user_type_id" in model._fields:
        values["user_type_id"] = self._map_user_type_id(record)

    return values
```

### Connector Odoo Cross-Version Pattern

```python
class AccountAccountImporter(Component):
    _inherit = "odoo.importer"
    _apply_on = "odoo.account.account"

    def _before_import(self):
        """Handle version-specific preparations."""
        record = self.odoo_record

        # Source might be Odoo 13 with user_type_id
        # Target might be Odoo 18 with account_type
        if "user_type_id" in record and "account_type" not in record:
            # Fetch the type from source and map it
            source_type = self._get_source_account_type(record["user_type_id"])
            record["account_type"] = self._map_to_target_type(source_type)
```
