# Frontend Reference

## XML Views

### Form View

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_model_name_form" model="ir.ui.view">
        <field name="name">model.name.form</field>
        <field name="model">model.name</field>
        <field name="arch" type="xml">
            <form string="Model Name">
                <header>
                    <button name="action_confirm" type="object"
                            string="Confirm" class="btn-primary"
                            invisible="state != 'draft'"/>
                    <button name="action_cancel" type="object"
                            string="Cancel"
                            invisible="state == 'done'"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,confirmed,done"/>
                </header>
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="action_view_orders" type="object"
                                class="oe_stat_button" icon="fa-list">
                            <field name="order_count" widget="statinfo"
                                   string="Orders"/>
                        </button>
                    </div>
                    <widget name="web_ribbon" title="Archived"
                            bg_color="bg-danger"
                            invisible="active"/>
                    <div class="oe_title">
                        <h1>
                            <field name="name" placeholder="Name"/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="partner_id"/>
                            <field name="date"/>
                        </group>
                        <group>
                            <field name="amount"/>
                            <field name="currency_id"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Lines" name="lines">
                            <field name="line_ids">
                                <tree editable="bottom">
                                    <field name="product_id"/>
                                    <field name="quantity"/>
                                    <field name="price"/>
                                    <field name="subtotal"/>
                                </tree>
                            </field>
                        </page>
                        <page string="Notes" name="notes">
                            <field name="notes" placeholder="Notes..."/>
                        </page>
                    </notebook>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="activity_ids"/>
                    <field name="message_ids"/>
                </div>
            </form>
        </field>
    </record>
</odoo>
```

### Tree/List View

```xml
<record id="view_model_name_tree" model="ir.ui.view">
    <field name="name">model.name.tree</field>
    <field name="model">model.name</field>
    <field name="arch" type="xml">
        <tree string="Model Names" multi_edit="1" sample="1">
            <field name="name"/>
            <field name="partner_id"/>
            <field name="date"/>
            <field name="state" widget="badge"
                   decoration-success="state == 'done'"
                   decoration-info="state == 'draft'"
                   decoration-warning="state == 'confirmed'"/>
            <field name="amount" sum="Total"/>
            <field name="company_id" groups="base.group_multi_company"/>
        </tree>
    </field>
</record>
```

### Search View

```xml
<record id="view_model_name_search" model="ir.ui.view">
    <field name="name">model.name.search</field>
    <field name="model">model.name</field>
    <field name="arch" type="xml">
        <search string="Search Model">
            <field name="name"/>
            <field name="partner_id"/>
            <filter name="filter_draft" string="Draft"
                    domain="[('state', '=', 'draft')]"/>
            <filter name="filter_my" string="My Records"
                    domain="[('user_id', '=', uid)]"/>
            <separator/>
            <filter name="filter_date" string="This Month"
                    domain="[('date', '&gt;=', (context_today() - relativedelta(day=1)).strftime('%Y-%m-%d'))]"/>
            <group expand="0" string="Group By">
                <filter name="group_partner" string="Partner"
                        context="{'group_by': 'partner_id'}"/>
                <filter name="group_state" string="Status"
                        context="{'group_by': 'state'}"/>
                <filter name="group_date" string="Date"
                        context="{'group_by': 'date:month'}"/>
            </group>
            <searchpanel>
                <field name="state" icon="fa-tasks"/>
                <field name="partner_id" select="multi"/>
            </searchpanel>
        </search>
    </field>
</record>
```

### Kanban View

```xml
<record id="view_model_name_kanban" model="ir.ui.view">
    <field name="name">model.name.kanban</field>
    <field name="model">model.name</field>
    <field name="arch" type="xml">
        <kanban default_group_by="state" class="o_kanban_small_column">
            <field name="name"/>
            <field name="partner_id"/>
            <field name="state"/>
            <field name="color"/>
            <templates>
                <t t-name="kanban-box">
                    <div t-attf-class="oe_kanban_card oe_kanban_global_click">
                        <div class="oe_kanban_content">
                            <div class="o_kanban_record_title">
                                <field name="name"/>
                            </div>
                            <div class="o_kanban_record_body">
                                <field name="partner_id"/>
                            </div>
                            <div class="o_kanban_record_bottom">
                                <div class="oe_kanban_bottom_left">
                                    <field name="date"/>
                                </div>
                                <div class="oe_kanban_bottom_right">
                                    <field name="amount" widget="monetary"/>
                                </div>
                            </div>
                        </div>
                    </div>
                </t>
            </templates>
        </kanban>
    </field>
</record>
```

### View Inheritance

```xml
<!-- Odoo 17+ syntax (no attrs) -->
<record id="view_partner_form_inherit" model="ir.ui.view">
    <field name="name">res.partner.form.inherit</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">
        <!-- Add field after existing field -->
        <field name="email" position="after">
            <field name="custom_field"/>
        </field>

        <!-- Add field with visibility -->
        <field name="phone" position="after">
            <field name="custom_field2" invisible="not is_company"/>
        </field>

        <!-- Replace field -->
        <field name="website" position="replace">
            <field name="website" widget="url" placeholder="https://"/>
        </field>

        <!-- Add to notebook -->
        <xpath expr="//notebook" position="inside">
            <page string="Custom" name="custom_page">
                <group>
                    <field name="custom_field"/>
                </group>
            </page>
        </xpath>

        <!-- Modify attributes -->
        <field name="name" position="attributes">
            <attribute name="required">True</attribute>
        </field>
    </field>
</record>
```

### Legacy Syntax (Odoo 16 and below)

```xml
<!-- attrs and states (deprecated in Odoo 17+) -->
<field name="custom_field"
       attrs="{'invisible': [('state', '!=', 'draft')],
               'required': [('type', '=', 'service')]}"/>

<button name="action_confirm" string="Confirm"
        states="draft"/>
```

## Actions

### Window Action

```xml
<record id="action_model_name" model="ir.actions.act_window">
    <field name="name">Model Names</field>
    <field name="res_model">model.name</field>
    <field name="view_mode">tree,form,kanban</field>
    <field name="domain">[('active', '=', True)]</field>
    <field name="context">{'default_state': 'draft'}</field>
    <field name="help" type="html">
        <p class="o_view_nocontent_smiling_face">
            Create your first record
        </p>
    </field>
</record>
```

### Server Action

```xml
<record id="action_server_process" model="ir.actions.server">
    <field name="name">Process Records</field>
    <field name="model_id" ref="model_model_name"/>
    <field name="binding_model_id" ref="model_model_name"/>
    <field name="binding_view_types">list,form</field>
    <field name="state">code</field>
    <field name="code">
        records.action_process()
    </field>
</record>
```

## QWeb Templates

### Report Template

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="report_model_name_document">
        <t t-call="web.external_layout">
            <t t-set="o" t-value="doc"/>
            <div class="page">
                <h2><t t-esc="o.name"/></h2>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        <t t-foreach="o.line_ids" t-as="line">
                            <tr>
                                <td><t t-esc="line.product_id.name"/></td>
                                <td><t t-esc="line.quantity"/></td>
                                <td><t t-esc="line.price" t-options="{'widget': 'monetary'}"/></td>
                            </tr>
                        </t>
                    </tbody>
                </table>
            </div>
        </t>
    </template>

    <template id="report_model_name">
        <t t-call="web.html_container">
            <t t-foreach="docs" t-as="doc">
                <t t-call="module_name.report_model_name_document"/>
            </t>
        </t>
    </template>
</odoo>
```

### Report Action

```xml
<record id="action_report_model_name" model="ir.actions.report">
    <field name="name">Print Report</field>
    <field name="model">model.name</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">module_name.report_model_name</field>
    <field name="report_file">module_name.report_model_name</field>
    <field name="binding_model_id" ref="model_model_name"/>
    <field name="binding_type">report</field>
</record>
```

## OWL Components (Odoo 14+)

### Basic Component (Odoo 16+)

```javascript
/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MyComponent extends Component {
    static template = "module_name.MyComponent";
    static props = {
        recordId: { type: Number },
        onSave: { type: Function, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            loading: false,
            data: null,
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            this.state.data = await this.orm.read(
                "model.name",
                [this.props.recordId],
                ["name", "state"]
            );
        } finally {
            this.state.loading = false;
        }
    }

    onButtonClick() {
        this.notification.add("Button clicked!", { type: "success" });
    }
}

registry.category("actions").add("my_action", MyComponent);
```

### OWL Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="module_name.MyComponent">
        <div class="my-component">
            <t t-if="state.loading">
                <div class="o_loading">Loading...</div>
            </t>
            <t t-else="">
                <div class="content">
                    <t t-esc="state.data?.name"/>
                </div>
                <button class="btn btn-primary" t-on-click="onButtonClick">
                    Click Me
                </button>
            </t>
        </div>
    </t>
</templates>
```

## Assets Declaration

### Odoo 14+ (__manifest__.py)

```python
{
    "assets": {
        "web.assets_backend": [
            "module_name/static/src/js/**/*.js",
            "module_name/static/src/css/**/*.css",
            "module_name/static/src/scss/**/*.scss",
            "module_name/static/src/xml/**/*.xml",
        ],
        "web.assets_frontend": [
            "module_name/static/src/js/frontend/*.js",
        ],
        "web.report_assets_common": [
            "module_name/static/src/css/report.css",
        ],
    },
}
```

### Odoo 13 and below (XML)

```xml
<template id="assets_backend" inherit_id="web.assets_backend">
    <xpath expr="." position="inside">
        <script type="text/javascript"
                src="/module_name/static/src/js/widget.js"/>
        <link rel="stylesheet"
              href="/module_name/static/src/css/style.css"/>
    </xpath>
</template>
```

## Common Widgets

| Widget | Field Type | Description |
|--------|------------|-------------|
| `char` | Char | Default text input |
| `text` | Text | Textarea |
| `html` | Html | Rich text editor |
| `integer` | Integer | Number input |
| `float` | Float | Decimal input |
| `monetary` | Monetary | Currency formatted |
| `date` | Date | Date picker |
| `datetime` | Datetime | Date/time picker |
| `selection` | Selection | Dropdown |
| `radio` | Selection | Radio buttons |
| `many2one` | Many2one | Dropdown with search |
| `many2many_tags` | Many2many | Tag chips |
| `many2many_checkboxes` | Many2many | Checkbox list |
| `one2many` | One2many | Inline list/table |
| `image` | Binary | Image display |
| `binary` | Binary | File upload |
| `url` | Char | Clickable link |
| `email` | Char | Email link |
| `phone` | Char | Phone link |
| `statusbar` | Selection | Status bar |
| `badge` | Selection | Colored badge |
| `priority` | Selection | Star rating |
| `color` | Integer | Color picker |
| `progressbar` | Float/Integer | Progress bar |
| `handle` | Integer | Drag handle (sequence) |
