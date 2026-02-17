from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round

class ProductTemplate(models.Model):
    """
    Extends Product Template to support secondary units of measure configuration.
    Allows defining a conversion ratio and tracking type for secondary units.
    """
    _inherit = 'product.template'

    enable_secondary_uom = fields.Boolean(
        "Enable Secondary UoM", 
        default=False,
        help="If checked, secondary units of measure fields will be available for this product."
    )
    secondary_uom_id = fields.Many2one(
        'uom.uom', 
        string="Secondary UoM",
        help="Select the secondary unit of measure for this product."
    )
    secondary_uom_ratio = fields.Float(
        "Secondary UoM Ratio", 
        digits='Product Unit of Measure', 
        default=1.0,
        help="Conversion factor between primary and secondary UoM. (Secondary = Primary * Ratio)"
    )
    secondary_uom_rounding = fields.Float(
        related='secondary_uom_id.rounding', 
        readonly=True,
        help="Rounding precision inherited from the secondary UoM definition."
    )
    secondary_tracking_type = fields.Selection([
        ('none', 'None'),
        ('stored', 'Stored'),
        ('computed', 'Computed')
    ], string="Secondary Tracking Type", default='none',
       help="Determines how the secondary quantity is managed.")

    @api.onchange('secondary_uom_id', 'uom_id')
    def _onchange_secondary_uom_id(self):
        """ Automatically computes the ratio if both UoMs belong to the same category. """
        if self.secondary_uom_id and self.uom_id:
            if self.secondary_uom_id._has_common_reference(self.uom_id):
                # Calculate ratio based on Odoo's standard conversion
                # e.g. 1 Unit = 0.1 Box (if ratio is 10)
                self.secondary_uom_ratio = self.uom_id._compute_quantity(1.0, self.secondary_uom_id)
            else:
                self.secondary_uom_ratio = 1.0

    @api.constrains('secondary_uom_id', 'uom_id')
    def _check_uom_category(self):
        """ Ensures that primary and secondary UoMs are in the same category hierarchy. """
        for template in self:
            if template.enable_secondary_uom and template.secondary_uom_id and template.uom_id:
                if not template.secondary_uom_id._has_common_reference(template.uom_id):
                    raise ValidationError(_("Secondary UoM must belong to same hierarchy as primary UoM."))

    @api.constrains('secondary_uom_ratio')
    def _check_secondary_uom_ratio(self):
        """ Prevents zero or negative conversion ratios. """
        for template in self:
            if template.enable_secondary_uom and template.secondary_uom_ratio <= 0:
                raise ValidationError(_("Secondary UoM Ratio must be greater than zero."))

    def convert_to_secondary(self, qty):
        """ Converts a primary quantity to secondary quantity using the ratio. """
        self.ensure_one()
        if not self.enable_secondary_uom or not self.secondary_uom_ratio:
            return qty
        return self.round_secondary(qty * self.secondary_uom_ratio)

    def convert_to_primary(self, qty):
        """ Converts a secondary quantity back to primary quantity. """
        self.ensure_one()
        if not self.enable_secondary_uom or not self.secondary_uom_ratio:
            return qty
        return qty / self.secondary_uom_ratio

    def round_secondary(self, qty):
        """ Rounds the secondary quantity based on the secondary UoM's precision. """
        self.ensure_one()
        rounding = self.secondary_uom_id.rounding or 0.01
        return float_round(qty, precision_rounding=rounding)

class ProductProduct(models.Model):
    """
    Extends Product Product to proxy conversion methods to the template.
    """
    _inherit = 'product.product'

    def convert_to_secondary(self, qty):
        return self.product_tmpl_id.convert_to_secondary(qty)

    def convert_to_primary(self, qty):
        return self.product_tmpl_id.convert_to_primary(qty)

    def round_secondary(self, qty):
        return self.product_tmpl_id.round_secondary(qty)
