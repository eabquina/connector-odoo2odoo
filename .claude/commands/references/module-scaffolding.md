# Module Scaffolding Reference

## Basic Module Structure

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
│   └── security.xml
├── data/
│   └── data.xml
├── demo/
│   └── demo.xml
├── wizards/
│   ├── __init__.py
│   └── wizard_name.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── static/
│   ├── description/
│   │   └── icon.png
│   └── src/
│       ├── js/
│       ├── css/
│       └── xml/
└── reports/
    ├── report_templates.xml
    └── report_actions.xml
```

## __manifest__.py (Odoo 10+)

```python
# Odoo 10-18+
{
    "name": "Module Name",
    "version": "18.0.1.0.0",  # <odoo_version>.<module_major>.<module_minor>.<module_patch>
    "category": "Category",
    "summary": "Short description",
    "description": """
Long description with features
==============================
* Feature 1
* Feature 2
    """,
    "author": "Your Company",
    "website": "https://yourcompany.com",
    "license": "LGPL-3",  # or AGPL-3 for OCA modules
    "depends": ["base", "sale"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/model_name_views.xml",
        "data/data.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "assets": {  # Odoo 14+
        "web.assets_backend": [
            "module_name/static/src/js/*.js",
            "module_name/static/src/css/*.css",
            "module_name/static/src/xml/*.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
```

### Legacy __openerp__.py (Odoo 8-9)

```python
{
    "name": "Module Name",
    "version": "8.0.1.0.0",
    "category": "Category",
    "depends": ["base"],
    "data": [
        "views/view.xml",
    ],
    "installable": True,
}
```

## __init__.py Files

### Root __init__.py

```python
from . import models
from . import wizards  # if exists
from . import controllers  # if exists
```

### models/__init__.py

```python
from . import model_name
from . import another_model
```

## Security Files

### security/ir.model.access.csv

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_model_name_user,model.name.user,model_model_name,base.group_user,1,1,1,0
access_model_name_manager,model.name.manager,model_model_name,module_name.group_manager,1,1,1,1
```

**Rules:**
- `id`: Unique XML ID (snake_case)
- `model_id:id`: `model_<model_name_with_underscores>`
- `group_id:id`: Reference to security group, empty for public access
- Permissions: 1 = granted, 0 = denied

### security/security.xml

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Security Groups -->
    <record id="group_user" model="ir.model.access">
        <field name="name">User</field>
        <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
    </record>

    <record id="group_manager" model="res.groups">
        <field name="name">Manager</field>
        <field name="implied_ids" eval="[(4, ref('module_name.group_user'))]"/>
        <field name="users" eval="[(4, ref('base.user_root')), (4, ref('base.user_admin'))]"/>
    </record>

    <!-- Record Rules (Multi-company) -->
    <record id="rule_model_multi_company" model="ir.rule">
        <field name="name">Model: Multi-Company</field>
        <field name="model_id" ref="model_model_name"/>
        <field name="domain_force">[
            '|',
            ('company_id', '=', False),
            ('company_id', 'in', company_ids)
        ]</field>
    </record>
</odoo>
```

## Menu Items

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Top Menu -->
    <menuitem id="menu_root"
              name="Module Name"
              sequence="10"/>

    <!-- Submenu -->
    <menuitem id="menu_model_name"
              name="Model Names"
              parent="menu_root"
              action="action_model_name"
              sequence="10"/>
</odoo>
```

## Data Files

### data/data.xml (Seed Data)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo noupdate="1">
    <record id="record_1" model="model.name">
        <field name="name">Record 1</field>
        <field name="active">True</field>
    </record>
</odoo>
```

**noupdate attribute:**
- `noupdate="1"`: Data won't be overwritten on module upgrade
- `noupdate="0"` (or omit): Data refreshed on every upgrade

## OCA Module Template

For OCA-compliant modules:

```
module_name/
├── __init__.py
├── __manifest__.py
├── README.rst           # Required for OCA
├── models/
├── views/
├── security/
├── static/
│   └── description/
│       ├── icon.png     # 128x128 PNG
│       └── index.html   # Auto-generated from README
├── tests/
│   ├── __init__.py
│   └── test_module_name.py
└── i18n/
    └── module_name.pot  # Translation template
```

### OCA Version Format

```
<odoo_major>.<odoo_minor>.<oca_major>.<oca_minor>.<oca_patch>
```

Example: `18.0.1.0.0`

## Post-Install Hooks

```python
# __manifest__.py
{
    ...
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "post_load": "post_load",  # Odoo 14+
}

# hooks.py (or __init__.py)
def pre_init_hook(env):
    """Runs before module installation."""
    pass

def post_init_hook(env):
    """Runs after module installation."""
    pass

def uninstall_hook(env):
    """Runs when module is uninstalled."""
    pass
```

## Scaffolding Command

```bash
# Create new module using Odoo scaffold
./odoo-bin scaffold module_name /path/to/addons

# Or with custom template
./odoo-bin scaffold -t /path/to/template module_name /path/to/addons
```
