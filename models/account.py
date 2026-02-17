from odoo import models, fields, api, _

class AccountMoveLine(models.Model):
    """
    Extends Account Move Line to support secondary quantities on invoices and bills.
    """
    _inherit = 'account.move.line'

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

    @api.depends('quantity', 'product_id', 'product_id.secondary_uom_ratio')
    def _compute_secondary_quantity(self):
        """ Computes secondary quantity whenever primary quantity or product settings change. """
        for line in self:
            if line.product_id.enable_secondary_uom:
                line.secondary_quantity = line.product_id.convert_to_secondary(line.quantity)
            else:
                line.secondary_quantity = 0.0

    def _inverse_secondary_quantity(self):
        """ Syncs primary quantity when secondary quantity is edited on the invoice line. """
        for line in self:
            if line.product_id.enable_secondary_uom and line.product_id.secondary_uom_ratio:
                line.quantity = line.product_id.convert_to_primary(line.secondary_quantity)
