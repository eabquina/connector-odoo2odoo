# ORM & Business Logic Reference

## Model Definition

### Basic Model (Odoo 10+)

```python
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ModelName(models.Model):
    _name = "model.name"
    _description = "Model Name"
    _inherit = ["mail.thread", "mail.activity.mixin"]  # Optional mixins
    _order = "sequence, name"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True, tracking=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
```

### Inheritance Patterns

```python
# Extension inheritance (add fields/methods to existing model)
class ResPartner(models.Model):
    _inherit = "res.partner"

    custom_field = fields.Char(string="Custom Field")


# Delegation inheritance (link to another model)
class ProductProduct(models.Model):
    _name = "product.product"
    _inherits = {"product.template": "product_tmpl_id"}

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        required=True,
        ondelete="cascade",
    )


# Abstract model (mixin, no database table)
class MailMixin(models.AbstractModel):
    _name = "mail.mixin"
    _description = "Mail Mixin"


# Transient model (wizard, auto-cleaned)
class MyWizard(models.TransientModel):
    _name = "my.wizard"
    _description = "My Wizard"
```

## Field Types

### Basic Fields

```python
# String fields
name = fields.Char(string="Name", size=100, trim=True)
description = fields.Text(string="Description")
html_content = fields.Html(string="HTML Content", sanitize=True)

# Numeric fields
quantity = fields.Integer(string="Quantity", default=0)
price = fields.Float(string="Price", digits=(16, 2))
amount = fields.Monetary(string="Amount", currency_field="currency_id")

# Date/Time fields
date = fields.Date(string="Date", default=fields.Date.today)
datetime = fields.Datetime(string="DateTime", default=fields.Datetime.now)

# Boolean
active = fields.Boolean(string="Active", default=True)

# Selection
state = fields.Selection(
    selection=[
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("done", "Done"),
    ],
    string="Status",
    default="draft",
    required=True,
)

# Binary
image = fields.Binary(string="Image", attachment=True)
document = fields.Binary(string="Document")
filename = fields.Char(string="Filename")
```

### Relational Fields

```python
# Many2one
partner_id = fields.Many2one(
    comodel_name="res.partner",
    string="Partner",
    required=True,
    ondelete="restrict",  # restrict, cascade, set null
    index=True,
    domain=[("is_company", "=", True)],
    context={"default_is_company": True},
)

# One2many
line_ids = fields.One2many(
    comodel_name="model.name.line",
    inverse_name="parent_id",
    string="Lines",
    copy=True,
)

# Many2many
tag_ids = fields.Many2many(
    comodel_name="model.tag",
    relation="model_name_tag_rel",  # Junction table name
    column1="model_id",
    column2="tag_id",
    string="Tags",
)
```

### Computed Fields

```python
# Computed field (stored)
total = fields.Float(
    string="Total",
    compute="_compute_total",
    store=True,
)

@api.depends("line_ids.subtotal")
def _compute_total(self):
    for record in self:
        record.total = sum(record.line_ids.mapped("subtotal"))


# Computed field (not stored, with inverse)
full_name = fields.Char(
    string="Full Name",
    compute="_compute_full_name",
    inverse="_inverse_full_name",
    search="_search_full_name",
)

@api.depends("first_name", "last_name")
def _compute_full_name(self):
    for record in self:
        record.full_name = f"{record.first_name} {record.last_name}"

def _inverse_full_name(self):
    for record in self:
        parts = (record.full_name or "").split(" ", 1)
        record.first_name = parts[0]
        record.last_name = parts[1] if len(parts) > 1 else ""

def _search_full_name(self, operator, value):
    return ["|", ("first_name", operator, value), ("last_name", operator, value)]
```

### Related Fields

```python
# Related field (shortcut to related model field)
partner_name = fields.Char(
    string="Partner Name",
    related="partner_id.name",
    store=True,  # Optional: store in database
    readonly=True,
)
```

## API Decorators

### Version Comparison

| Decorator | Odoo 8-12 | Odoo 13+ |
|-----------|-----------|----------|
| `@api.multi` | Required for recordsets | Removed (default behavior) |
| `@api.one` | Single record | Removed |
| `@api.model` | Class method | Still used |
| `@api.depends` | Compute triggers | Still used |
| `@api.constrains` | Validation | Still used |
| `@api.onchange` | UI changes | Still used |

### Current Decorators (Odoo 13+)

```python
@api.model
def create(self, vals):
    """Override create - class method."""
    return super().create(vals)

@api.depends("field1", "field2")
def _compute_field(self):
    """Triggered when dependencies change."""
    for record in self:
        record.computed_field = record.field1 + record.field2

@api.constrains("field1", "field2")
def _check_fields(self):
    """Validation constraint."""
    for record in self:
        if record.field1 < 0:
            raise ValidationError(_("Field1 must be positive."))

@api.onchange("partner_id")
def _onchange_partner_id(self):
    """UI-only change, not saved to DB."""
    if self.partner_id:
        self.name = self.partner_id.name
    return {"warning": {"title": "Warning", "message": "Check partner"}}

@api.model_create_multi  # Odoo 12+
def create(self, vals_list):
    """Batch create optimization."""
    return super().create(vals_list)
```

## CRUD Operations

### Create

```python
# Single record
record = self.env["model.name"].create({
    "name": "New Record",
    "partner_id": partner.id,
})

# Multiple records (Odoo 12+)
records = self.env["model.name"].create([
    {"name": "Record 1"},
    {"name": "Record 2"},
])

# With context
record = self.env["model.name"].with_context(no_check=True).create(vals)
```

### Read / Search

```python
# Search
records = self.env["model.name"].search([
    ("state", "=", "draft"),
    ("date", ">=", "2024-01-01"),
], limit=10, order="date desc")

# Search and read (returns list of dicts)
data = self.env["model.name"].search_read(
    domain=[("active", "=", True)],
    fields=["name", "date"],
    limit=100,
)

# Browse by IDs
records = self.env["model.name"].browse([1, 2, 3])

# Read specific fields
values = record.read(["name", "state"])

# Search count
count = self.env["model.name"].search_count([("state", "=", "draft")])
```

### Update

```python
# Single field
record.name = "New Name"

# Multiple fields
record.write({
    "name": "New Name",
    "state": "confirmed",
})

# Update multiple records
records.write({"active": False})

# One2many/Many2many special commands
record.write({
    "line_ids": [
        (0, 0, {"name": "New line"}),      # Create
        (1, line_id, {"name": "Updated"}),  # Update
        (2, line_id, 0),                    # Delete
        (3, line_id, 0),                    # Unlink (M2M only)
        (4, line_id, 0),                    # Link (M2M only)
        (5, 0, 0),                          # Unlink all
        (6, 0, [id1, id2]),                 # Replace all
    ],
})
```

### Delete

```python
# Delete records
records.unlink()

# Archive instead of delete
records.write({"active": False})
```

## Domain Filters

```python
# Operators
[("field", "=", value)]       # Equal
[("field", "!=", value)]      # Not equal
[("field", ">", value)]       # Greater than
[("field", ">=", value)]      # Greater or equal
[("field", "<", value)]       # Less than
[("field", "<=", value)]      # Less or equal
[("field", "in", [1, 2, 3])]  # In list
[("field", "not in", [1, 2])] # Not in list
[("field", "like", "%value%")]     # SQL LIKE
[("field", "ilike", "%value%")]    # Case-insensitive LIKE
[("field", "=like", "value%")]     # Pattern match
[("field", "=ilike", "value%")]    # Case-insensitive pattern
[("field", "child_of", parent_id)] # Hierarchical
[("field", "parent_of", child_id)] # Hierarchical (reverse)

# Logical operators
["&", ("a", "=", 1), ("b", "=", 2)]  # AND (default)
["|", ("a", "=", 1), ("b", "=", 2)]  # OR
["!", ("a", "=", 1)]                  # NOT

# Complex example
[
    "&",
    "|",
    ("state", "=", "draft"),
    ("state", "=", "sent"),
    ("date", ">=", "2024-01-01"),
]
```

## Constraints

### SQL Constraints

```python
class ModelName(models.Model):
    _name = "model.name"

    _sql_constraints = [
        ("name_unique", "UNIQUE(name)", "Name must be unique!"),
        ("check_quantity", "CHECK(quantity >= 0)", "Quantity must be positive!"),
        ("name_company_unique", "UNIQUE(name, company_id)", "Name must be unique per company!"),
    ]
```

### Python Constraints

```python
@api.constrains("date_start", "date_end")
def _check_dates(self):
    for record in self:
        if record.date_start and record.date_end:
            if record.date_start > record.date_end:
                raise ValidationError(_("Start date must be before end date."))
```

## Wizards (Transient Models)

```python
class MyWizard(models.TransientModel):
    _name = "my.wizard"
    _description = "My Wizard"

    partner_id = fields.Many2one("res.partner", required=True)
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Process wizard and return action."""
        self.ensure_one()
        # Do something
        active_ids = self.env.context.get("active_ids", [])
        records = self.env["sale.order"].browse(active_ids)
        records.write({"partner_id": self.partner_id.id})

        # Return action or close wizard
        return {"type": "ir.actions.act_window_close"}
```

## Scheduled Actions (Cron)

```xml
<record id="ir_cron_process_records" model="ir.cron">
    <field name="name">Process Records Daily</field>
    <field name="model_id" ref="model_model_name"/>
    <field name="state">code</field>
    <field name="code">model._cron_process_records()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
    <field name="numbercall">-1</field>
    <field name="active">True</field>
</record>
```

```python
@api.model
def _cron_process_records(self):
    """Called by scheduled action."""
    records = self.search([("state", "=", "pending")])
    for record in records:
        record.action_process()
```

## Environment & Context

```python
# Access environment
self.env.user          # Current user
self.env.company       # Current company (Odoo 13+)
self.env.companies     # All allowed companies (Odoo 13+)
self.env.uid           # Current user ID
self.env.cr            # Database cursor
self.env.context       # Context dict

# Odoo 12 and below
self.env.user.company_id  # Current company

# Change context
self.with_context(key=value)
self.with_context(**new_context)
self.env["model"].with_context(lang="fr_FR")

# Change user
self.sudo()                    # Superuser
self.with_user(user_id)        # Specific user

# Change company
self.with_company(company_id)  # Odoo 13+
```
