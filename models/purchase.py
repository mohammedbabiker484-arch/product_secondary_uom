from odoo import models, fields, api, _

class PurchaseOrderLine(models.Model):
    """
    Extends Purchase Order Line to support secondary quantities.
    Enables tracking of purchases in alternative units (e.g., buying in boxes but storing in units).
    """
    _inherit = 'purchase.order.line'

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

    @api.depends('product_qty', 'product_id', 'product_id.secondary_uom_ratio')
    def _compute_secondary_quantity(self):
        """ Computes secondary quantity whenever purchase quantity or product settings change. """
        for line in self:
            if line.product_id.enable_secondary_uom:
                line.secondary_quantity = line.product_id.convert_to_secondary(line.product_qty)
            else:
                line.secondary_quantity = 0.0

    def _inverse_secondary_quantity(self):
        """ Computes primary quantity when secondary quantity is edited. """
        for line in self:
            if line.product_id.enable_secondary_uom and line.product_id.secondary_uom_ratio:
                line.product_qty = line.product_id.convert_to_primary(line.secondary_quantity)

    @api.onchange('secondary_quantity')
    def _onchange_secondary_quantity(self):
        """ UI feedback for secondary quantity changes. """
        if self.product_id.enable_secondary_uom and self.product_id.secondary_uom_ratio:
            self.product_qty = self.product_id.convert_to_primary(self.secondary_quantity)

    @api.onchange('product_qty')
    def _onchange_product_qty_sec(self):
        """ UI feedback for primary quantity changes. """
        if self.product_id.enable_secondary_uom:
            self.secondary_quantity = self.product_id.convert_to_secondary(self.product_qty)
