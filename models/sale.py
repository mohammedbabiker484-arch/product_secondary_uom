from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    """
    Extends Sale Order Line to support secondary quantities.
    The secondary quantity is synchronized with the primary quantity based on the product's ratio.
    """
    _inherit = 'sale.order.line'

    secondary_quantity = fields.Float(
        string="Secondary Qty", 
        digits='Product Unit of Measure', 
        compute='_compute_secondary_quantity', 
        inverse='_inverse_secondary_quantity', 
        store=True,
        help="Quantity in the secondary unit of measure."
    )
    secondary_uom_id = fields.Many2one(
        related='product_id.secondary_uom_id', 
        string="Secondary UoM", 
        readonly=True,
        help="Secondary unit of measure defined on the product."
    )

    @api.depends('product_uom_qty', 'product_id', 'product_id.secondary_uom_ratio')
    def _compute_secondary_quantity(self):
        """ Computes secondary quantity whenever primary quantity or product settings change. """
        for line in self:
            if line.product_id.enable_secondary_uom:
                line.secondary_quantity = line.product_id.convert_to_secondary(line.product_uom_qty)
            else:
                line.secondary_quantity = 0.0

    def _inverse_secondary_quantity(self):
        """ Computes primary quantity when secondary quantity is manually edited. """
        for line in self:
            if line.product_id.enable_secondary_uom and line.product_id.secondary_uom_ratio:
                line.product_uom_qty = line.product_id.convert_to_primary(self.secondary_quantity)

    @api.onchange('secondary_quantity')
    def _onchange_secondary_quantity(self):
        """ Immediate feedback in the UI when editing secondary quantity. """
        if self.product_id.enable_secondary_uom and self.product_id.secondary_uom_ratio:
            self.product_uom_qty = self.product_id.convert_to_primary(self.secondary_quantity)

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty_sec(self):
        """ Immediate feedback in the UI when editing primary quantity. """
        if self.product_id.enable_secondary_uom:
            self.secondary_quantity = self.product_id.convert_to_secondary(self.product_uom_qty)

    def _prepare_invoice_line(self, **optional_values):
        """ Passes the secondary quantity to the invoice line during the invoicing process. """
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if self.product_id.enable_secondary_uom:
            res.update({
                'secondary_quantity': self.secondary_quantity,
            })
        return res

    def _prepare_procurement_values(self):
        """ Passes the secondary quantity to procurement/stock moves. """
        res = super()._prepare_procurement_values()
        if self.product_id.enable_secondary_uom:
            res.update({
                'secondary_qty': self.secondary_quantity,
            })
        return res
