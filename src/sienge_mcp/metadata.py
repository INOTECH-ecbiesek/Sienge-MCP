"""
MCP Server Metadata for Smithery Compatibility
"""

__version__ = "1.1.5"
__name__ = "sienge-ecbiesek-mcp"
__title__ = "Sienge ERP Integration"
__description__ = "Model Context Protocol server for Sienge API integration"
__author__ = "ECBIESEK"
__author_email__ = "ti@ecbiesek.com"
__license__ = "MIT"
__url__ = "https://github.com/INOTECH-ecbiesek/Sienge-MCP"

# MCP Capabilities
MCP_CAPABILITIES = {
    "tools": [
        "test_sienge_connection",
        "get_sienge_accounts_receivable", 
        "get_sienge_projects",
        "get_sienge_purchase_requests",
        "get_sienge_purchase_invoice",
        "get_sienge_purchase_invoice_items",
        "create_sienge_purchase_invoice",
        "add_items_to_purchase_invoice",
        "get_sienge_customers"
    ],
    "resources": [],
    "prompts": []
}

# Required environment variables
REQUIRED_ENV_VARS = [
    "SIENGE_SUBDOMAIN",
    "SIENGE_USERNAME", 
    "SIENGE_PASSWORD"
]

# Optional environment variables
OPTIONAL_ENV_VARS = [
    "SIENGE_BASE_URL",
    "SIENGE_API_KEY", 
    "SIENGE_TIMEOUT"
]