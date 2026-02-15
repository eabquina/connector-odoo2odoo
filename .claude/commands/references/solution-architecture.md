# Solution Architecture Reference

## Multi-Module Design Patterns

### Module Dependency Layers

```
┌─────────────────────────────────────────┐
│         Customer-Specific Modules        │  customer_acme_*
│         (business customizations)        │
├─────────────────────────────────────────┤
│         Vertical Modules                 │  industry_*, vertical_*
│         (industry-specific features)     │
├─────────────────────────────────────────┤
│         Connector/Integration Modules    │  connector_*, integration_*
│         (external system bridges)        │
├─────────────────────────────────────────┤
│         Extension Modules                │  sale_*, purchase_*, account_*
│         (extend standard Odoo)           │
├─────────────────────────────────────────┤
│         Base/Technical Modules           │  base_*, web_*
│         (shared utilities)               │
├─────────────────────────────────────────┤
│         OCA Community Modules            │  (from OCA repositories)
├─────────────────────────────────────────┤
│         Odoo Standard Modules            │  (from Odoo core)
└─────────────────────────────────────────┘
```

### Module Splitting Guidelines

**When to split into separate modules:**
- Different functional domains (sales vs. inventory)
- Optional features that not all customers need
- Integration with external systems
- Features requiring different licenses (LGPL vs AGPL)
- Features with heavy dependencies (avoid pulling in unnecessary modules)

**When to keep in one module:**
- Tightly coupled features that always go together
- Simple customizations to a single model
- Features that make no sense independently

### Naming Conventions

```
# Extending standard modules
sale_custom_field          # Adding fields to sale.order
sale_margin_report         # Adding margin reporting to sales
account_invoice_merge      # Invoice merging feature

# New functionality on top of standard
sale_subscription          # Subscription management (built on sale)
purchase_requisition       # Purchase requisition workflow

# Integration modules
connector_ecommerce        # E-commerce connector base
connector_magento          # Magento-specific connector
connector_shopify          # Shopify-specific connector

# Customer-specific
acme_sale_workflow         # Acme's custom sale workflow
acme_inventory_rules       # Acme's inventory rules
```

## Data Model Planning

### Model Relationship Patterns

```
┌──────────────────┐
│   res.partner    │◄────────────────────────────────┐
└────────┬─────────┘                                 │
         │                                           │
         │ partner_id                                │ partner_id
         ▼                                           │
┌──────────────────┐      order_id      ┌───────────┴──────────┐
│   sale.order     │◄───────────────────│   sale.order.line    │
└────────┬─────────┘                    └───────────┬──────────┘
         │                                          │
         │ sale_id                                  │ product_id
         ▼                                          ▼
┌──────────────────┐                    ┌──────────────────────┐
│   stock.picking  │                    │   product.product    │
└──────────────────┘                    └──────────────────────┘
```

### Field Type Selection Guide

| Requirement | Field Type | Notes |
|-------------|------------|-------|
| Simple text, < 255 chars | `Char` | Use `size` param for DB constraint |
| Long text, notes | `Text` | No size limit |
| Rich text with formatting | `Html` | Use `sanitize=True` |
| Whole numbers | `Integer` | |
| Decimal numbers | `Float` | Use `digits=(precision, scale)` |
| Money amounts | `Monetary` | Requires `currency_field` |
| Yes/No | `Boolean` | |
| Predefined options | `Selection` | Extensible via `selection_add` |
| Date only | `Date` | |
| Date and time | `Datetime` | Always stored in UTC |
| Link to another model | `Many2one` | Consider `ondelete` behavior |
| List of linked records | `Many2many` | Specify relation table name |
| Child records | `One2many` | Always has inverse `Many2one` |
| File/image | `Binary` | Use `attachment=True` for filestore |

### Multi-Company Architecture

```python
class MyModel(models.Model):
    _name = "my.model"
    _description = "My Model"

    # Company field (required for multi-company)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # For shared records (optional company)
    # company_id = fields.Many2one(
    #     comodel_name="res.company",
    #     string="Company",
    #     default=lambda self: self.env.company,
    # )
```

**Record Rules for Multi-Company:**

```xml
<record id="rule_my_model_company" model="ir.rule">
    <field name="name">My Model: Company Access</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="domain_force">[
        '|',
        ('company_id', '=', False),
        ('company_id', 'in', company_ids)
    ]</field>
</record>
```

## Performance Optimization

### Database Indexes

```python
class MyModel(models.Model):
    _name = "my.model"

    # Single field index
    reference = fields.Char(index=True)

    # Many2one always indexed by default
    partner_id = fields.Many2one("res.partner")

    # Composite index via SQL constraint
    _sql_constraints = [
        # Creates index automatically
        ("unique_ref_company", "UNIQUE(reference, company_id)", "..."),
    ]

    def init(self):
        """Create custom indexes."""
        self.env.cr.execute("""
            CREATE INDEX IF NOT EXISTS my_model_date_state_idx
            ON my_model (date, state)
            WHERE active = true
        """)
```

### Query Optimization

```python
# BAD: N+1 queries
for order in orders:
    print(order.partner_id.name)  # Query per order

# GOOD: Prefetch related records
orders = self.env["sale.order"].search([])
orders.mapped("partner_id")  # Single query for all partners
for order in orders:
    print(order.partner_id.name)  # No additional queries

# GOOD: Use read() for bulk data
data = orders.read(["name", "partner_id", "amount_total"])

# GOOD: Use search_read() when you don't need recordsets
data = self.env["sale.order"].search_read(
    domain=[("state", "=", "sale")],
    fields=["name", "partner_id", "amount_total"],
    limit=1000,
)

# GOOD: Use SQL for complex aggregations
self.env.cr.execute("""
    SELECT partner_id, SUM(amount_total) as total
    FROM sale_order
    WHERE state = 'sale'
    GROUP BY partner_id
""")
results = self.env.cr.dictfetchall()
```

### Computed Field Optimization

```python
# Store computed fields when:
# - Value doesn't change often
# - Used in search/filter/groupby
# - Expensive to compute
total = fields.Float(compute="_compute_total", store=True)

# Don't store when:
# - Value changes frequently
# - Based on current date/time
# - Light computation
display_name = fields.Char(compute="_compute_display_name")

# Use compute_sudo for cross-company computed fields
partner_credit = fields.Float(compute="_compute_credit", compute_sudo=True)
```

### Batch Processing

```python
# Process large datasets in batches
def process_large_dataset(self):
    batch_size = 1000
    offset = 0

    while True:
        records = self.search([], limit=batch_size, offset=offset)
        if not records:
            break

        for record in records:
            record._process_single()

        # Commit batch and clear cache
        self.env.cr.commit()
        self.env.invalidate_all()

        offset += batch_size

# Use queue_job for async processing
def process_async(self):
    for record in self:
        record.with_delay().process_single()
```

## Upgrade Strategy

### Migration Scripts

```
module_name/
├── migrations/
│   ├── 14.0.1.0.0/
│   │   ├── pre-migration.py
│   │   └── post-migration.py
│   └── 14.0.2.0.0/
│       └── post-migration.py
```

**pre-migration.py** (runs before module update):

```python
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Rename columns before ORM touches them
    openupgrade.rename_columns(env.cr, {
        "my_table": [
            ("old_column", "new_column"),
        ],
    })

    # Rename fields
    openupgrade.rename_fields(env, [
        ("my.model", "my_model", "old_field", "new_field"),
    ])
```

**post-migration.py** (runs after module update):

```python
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Data transformations
    env.cr.execute("""
        UPDATE my_model
        SET new_field = old_value * 100
        WHERE new_field IS NULL
    """)

    # Recompute stored fields
    records = env["my.model"].search([])
    records._compute_some_field()
```

### Version Numbering

```
<odoo_version>.<major>.<minor>.<patch>

# Examples:
14.0.1.0.0  # Initial release for Odoo 14
14.0.1.1.0  # Minor feature addition
14.0.1.1.1  # Bug fix
14.0.2.0.0  # Breaking change (requires migration)
```

## Security Architecture

### Access Control Layers

```
1. Model Access (ir.model.access.csv)
   └── Can user CRUD this model at all?

2. Record Rules (ir.rule)
   └── Which records can user see/modify?

3. Field Groups (groups= attribute)
   └── Can user see/edit this field?

4. Menu/Action Access (groups= attribute)
   └── Can user access this menu/action?

5. Business Logic (Python checks)
   └── Custom permission checks in code
```

### Security Best Practices

```python
# Always use sudo() sparingly and explicitly
def action_approve(self):
    # Check permission first
    if not self.env.user.has_group("module.group_approver"):
        raise AccessError(_("Only approvers can approve."))

    # Then use sudo for system operations
    self.sudo().write({"state": "approved"})

# Avoid bypassing security in searches
# BAD
records = self.env["sensitive.model"].sudo().search([])

# GOOD - let record rules filter
records = self.env["sensitive.model"].search([])

# Check access explicitly
self.check_access_rights("write")
self.check_access_rule("write")
```

## Testing Strategy

### Test Structure

```
module_name/
├── tests/
│   ├── __init__.py
│   ├── common.py           # Shared test setup
│   ├── test_model_name.py  # Model tests
│   └── test_wizard.py      # Wizard tests
```

### Test Classes

```python
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMyModel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.model = cls.env["my.model"]

    def test_create_record(self):
        """Test record creation."""
        record = self.model.create({
            "name": "Test",
            "partner_id": self.partner.id,
        })
        self.assertEqual(record.name, "Test")
        self.assertEqual(record.state, "draft")

    def test_compute_total(self):
        """Test computed field."""
        record = self.model.create({
            "name": "Test",
            "line_ids": [
                (0, 0, {"quantity": 2, "price": 10}),
                (0, 0, {"quantity": 3, "price": 20}),
            ],
        })
        self.assertEqual(record.total, 80.0)

    def test_constraint_validation(self):
        """Test constraint raises error."""
        with self.assertRaises(ValidationError):
            self.model.create({
                "name": "Test",
                "quantity": -1,  # Should fail constraint
            })
```

### Running Tests

```bash
# Run all tests for a module
./odoo-bin -c odoo.conf -d test_db --test-enable -i module_name --stop-after-init

# Run specific test class
./odoo-bin -c odoo.conf -d test_db --test-enable --test-tags=/module_name:TestMyModel

# Run with coverage
coverage run ./odoo-bin -c odoo.conf -d test_db --test-enable -i module_name --stop-after-init
coverage report
```
