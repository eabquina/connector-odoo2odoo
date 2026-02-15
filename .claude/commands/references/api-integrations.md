# API & Integrations Reference

## XML-RPC (Standard Odoo API)

### Python Client

```python
import xmlrpc.client

# Connection settings
url = "https://odoo.example.com"
db = "database_name"
username = "admin"
password = "admin_password"  # Or API key

# Authenticate
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

# Get models proxy
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Execute methods
def execute(model, method, *args, **kwargs):
    return models.execute_kw(db, uid, password, model, method, args, kwargs)

# Search
partner_ids = execute("res.partner", "search", [
    [("is_company", "=", True)],
], limit=10)

# Read
partners = execute("res.partner", "read", [partner_ids], {"fields": ["name", "email"]})

# Search and read
partners = execute("res.partner", "search_read", [
    [("is_company", "=", True)],
], {"fields": ["name", "email"], "limit": 10})

# Create
new_id = execute("res.partner", "create", [{
    "name": "New Partner",
    "email": "partner@example.com",
}])

# Write
execute("res.partner", "write", [[new_id], {"phone": "123456789"}])

# Unlink
execute("res.partner", "unlink", [[new_id]])

# Call custom method
result = execute("sale.order", "action_confirm", [[order_id]])
```

### OdooRPC Library

```python
import odoorpc

# Connect
odoo = odoorpc.ODOO("odoo.example.com", port=443, protocol="jsonrpc+ssl")
odoo.login("database_name", "admin", "password")

# Access models
Partner = odoo.env["res.partner"]

# Search
partner_ids = Partner.search([("is_company", "=", True)], limit=10)

# Browse (lazy loading)
partners = Partner.browse(partner_ids)
for partner in partners:
    print(partner.name, partner.email)

# Create
new_id = Partner.create({"name": "New Partner"})

# Write
partner = Partner.browse(new_id)
partner.email = "new@example.com"

# Read
data = Partner.read(partner_ids, ["name", "email"])

# Execute workflow/methods
odoo.execute("sale.order", "action_confirm", [order_id])
```

## JSON-RPC

### Python Client

```python
import requests
import json

url = "https://odoo.example.com"
db = "database_name"
username = "admin"
password = "password"

def json_rpc(endpoint, method, params):
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    response = requests.post(
        f"{url}{endpoint}",
        json=data,
        headers={"Content-Type": "application/json"},
    )
    result = response.json()
    if "error" in result:
        raise Exception(result["error"])
    return result.get("result")

# Authenticate
uid = json_rpc("/jsonrpc", "call", {
    "service": "common",
    "method": "authenticate",
    "args": [db, username, password, {}],
})

# Call model methods
def call_model(model, method, args=None, kwargs=None):
    return json_rpc("/jsonrpc", "call", {
        "service": "object",
        "method": "execute_kw",
        "args": [db, uid, password, model, method, args or [], kwargs or {}],
    })

# Search read
partners = call_model("res.partner", "search_read",
    [[("is_company", "=", True)]],
    {"fields": ["name", "email"], "limit": 10}
)
```

### JavaScript Client

```javascript
async function jsonRpc(url, method, params) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: method,
            params: params,
            id: Math.floor(Math.random() * 1000000),
        }),
    });
    const result = await response.json();
    if (result.error) throw new Error(result.error.message);
    return result.result;
}

// Authenticate
const uid = await jsonRpc('/jsonrpc', 'call', {
    service: 'common',
    method: 'authenticate',
    args: ['database', 'admin', 'password', {}],
});

// Call model
async function callModel(model, method, args = [], kwargs = {}) {
    return jsonRpc('/jsonrpc', 'call', {
        service: 'object',
        method: 'execute_kw',
        args: ['database', uid, 'password', model, method, args, kwargs],
    });
}

// Usage
const partners = await callModel('res.partner', 'search_read',
    [[['is_company', '=', true]]],
    {fields: ['name', 'email'], limit: 10}
);
```

## REST API (Custom Controllers)

### HTTP Controller

```python
from odoo import http
from odoo.http import request, Response
import json


class MyApiController(http.Controller):

    @http.route("/api/v1/partners", type="json", auth="user", methods=["GET"])
    def get_partners(self, **kwargs):
        """JSON endpoint (expects JSON body, returns JSON)."""
        partners = request.env["res.partner"].search_read(
            [("is_company", "=", True)],
            ["name", "email"],
            limit=kwargs.get("limit", 100),
        )
        return {"status": "success", "data": partners}

    @http.route("/api/v1/partners/<int:partner_id>", type="json", auth="user", methods=["GET"])
    def get_partner(self, partner_id, **kwargs):
        """Get single partner."""
        partner = request.env["res.partner"].browse(partner_id)
        if not partner.exists():
            return {"status": "error", "message": "Partner not found"}
        return {
            "status": "success",
            "data": {
                "id": partner.id,
                "name": partner.name,
                "email": partner.email,
            },
        }

    @http.route("/api/v1/partners", type="json", auth="user", methods=["POST"])
    def create_partner(self, **kwargs):
        """Create partner from JSON body."""
        vals = {
            "name": kwargs.get("name"),
            "email": kwargs.get("email"),
        }
        partner = request.env["res.partner"].create(vals)
        return {"status": "success", "id": partner.id}

    @http.route("/api/v1/public/info", type="http", auth="public", methods=["GET"])
    def public_info(self, **kwargs):
        """HTTP endpoint (returns raw response)."""
        data = {"version": "1.0", "status": "ok"}
        return Response(
            json.dumps(data),
            content_type="application/json",
            status=200,
        )

    @http.route("/api/v1/webhook", type="json", auth="public", methods=["POST"], csrf=False)
    def webhook(self, **kwargs):
        """Webhook endpoint (no CSRF, public auth)."""
        # Process webhook payload
        payload = kwargs
        # Validate signature, process data, etc.
        return {"received": True}
```

### Authentication Types

```python
# Session-based (default web)
@http.route("/api/v1/endpoint", auth="user")

# API Key / Token (Odoo 14+)
@http.route("/api/v1/endpoint", auth="api_key")

# Public (no auth)
@http.route("/api/v1/endpoint", auth="public")

# Custom auth
@http.route("/api/v1/endpoint", auth="custom_auth")
```

## External ID (XML ID) Operations

```python
# Get record by XML ID
partner = self.env.ref("base.res_partner_1")

# Get XML ID of record
xml_id = partner.get_external_id().get(partner.id)

# Create with XML ID
self.env["ir.model.data"].create({
    "name": "my_partner_1",
    "module": "my_module",
    "model": "res.partner",
    "res_id": partner.id,
})

# Search by XML ID via RPC
models.execute_kw(db, uid, password, "ir.model.data", "search_read", [
    [("module", "=", "base"), ("name", "=", "res_partner_1")],
], {"fields": ["res_id"]})
```

## Connector Framework (OCA)

### Backend Model

```python
from odoo import fields, models


class MyBackend(models.Model):
    _name = "my.backend"
    _description = "My External System Backend"
    _inherit = "connector.backend"

    name = fields.Char(required=True)
    location = fields.Char(string="URL", required=True)
    username = fields.Char()
    password = fields.Char()
    version = fields.Selection([
        ("1.0", "Version 1.0"),
        ("2.0", "Version 2.0"),
    ], default="2.0")
```

### Binding Model

```python
class MyProductBinding(models.Model):
    _name = "my.product.product"
    _description = "My Product Binding"
    _inherit = "external.binding"
    _inherits = {"product.product": "odoo_id"}

    odoo_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
        ondelete="cascade",
    )
    backend_id = fields.Many2one(
        comodel_name="my.backend",
        string="Backend",
        required=True,
        ondelete="restrict",
    )
    external_id = fields.Char(string="External ID")
```

### Adapter Component

```python
from odoo.addons.component.core import Component


class MyProductAdapter(Component):
    _name = "my.product.adapter"
    _inherit = "base.backend.adapter"
    _apply_on = "my.product.product"

    def search(self, filters=None):
        """Search external records."""
        # Call external API
        return self.backend_record._call("products/search", filters)

    def read(self, external_id):
        """Read single external record."""
        return self.backend_record._call(f"products/{external_id}")

    def create(self, data):
        """Create external record."""
        return self.backend_record._call("products", method="POST", data=data)

    def write(self, external_id, data):
        """Update external record."""
        return self.backend_record._call(f"products/{external_id}", method="PUT", data=data)
```

### Importer Component

```python
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class MyProductImporter(Component):
    _name = "my.product.importer"
    _inherit = "base.importer"
    _apply_on = "my.product.product"

    def _import(self, external_id, force=False):
        """Import a record from external system."""
        adapter = self.component(usage="backend.adapter")
        external_data = adapter.read(external_id)

        mapper = self.component(usage="import.mapper")
        map_record = mapper.map_record(external_data)

        binding = self._get_binding()
        if binding:
            binding.write(map_record.values())
        else:
            binding = self.model.create(map_record.values(for_create=True))

        return binding


class MyProductImportMapper(Component):
    _name = "my.product.import.mapper"
    _inherit = "base.import.mapper"
    _apply_on = "my.product.product"

    direct = [
        ("name", "name"),
        ("sku", "default_code"),
        ("price", "list_price"),
    ]

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def category(self, record):
        # Complex mapping logic
        category_name = record.get("category")
        category = self.env["product.category"].search([
            ("name", "=", category_name),
        ], limit=1)
        return {"categ_id": category.id if category else False}
```

## Webhook Handling

```python
import hashlib
import hmac

from odoo import http
from odoo.http import request


class WebhookController(http.Controller):

    @http.route("/webhook/external", type="json", auth="public",
                methods=["POST"], csrf=False)
    def handle_webhook(self, **kwargs):
        # Verify signature
        secret = request.env["ir.config_parameter"].sudo().get_param(
            "webhook.secret"
        )
        signature = request.httprequest.headers.get("X-Signature")

        if not self._verify_signature(request.jsonrequest, secret, signature):
            return {"error": "Invalid signature"}, 403

        # Process event
        event_type = kwargs.get("event")
        data = kwargs.get("data", {})

        if event_type == "order.created":
            self._handle_order_created(data)
        elif event_type == "order.updated":
            self._handle_order_updated(data)

        return {"status": "ok"}

    def _verify_signature(self, payload, secret, signature):
        if not secret or not signature:
            return False
        expected = hmac.new(
            secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _handle_order_created(self, data):
        request.env["sale.order"].sudo().with_delay().create_from_webhook(data)
```

## Queue Job Integration

```python
from odoo import models
from odoo.addons.queue_job.job import job


class ProductProduct(models.Model):
    _inherit = "product.product"

    @job(default_channel="root.imports")
    def import_from_external(self, backend_id, external_id):
        """Async job to import product."""
        backend = self.env["my.backend"].browse(backend_id)
        with backend.work_on("my.product.product") as work:
            importer = work.component(usage="record.importer")
            importer.run(external_id)

    def button_import(self):
        """Trigger async import."""
        for record in self:
            record.with_delay(
                priority=10,
                eta=60,  # Start after 60 seconds
                max_retries=3,
            ).import_from_external(
                self.backend_id.id,
                self.external_id,
            )
```
