{
    'name': 'Product Secondary UoM Lifecycle',
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Full lifecycle support for Secondary Unit of Measure',
    'description': """
        Implements a complete Secondary Unit of Measure (Secondary UoM) system fully integrated into:
        Product → Purchase → Inventory → Sales → Accounting.
    """,
    'author': 'Mohammed Gameel',
    'depends': ['product', 'purchase', 'sale_stock', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'views/stock_views.xml',
        'views/account_views.xml',
        'views/reports.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
