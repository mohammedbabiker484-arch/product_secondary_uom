from odoo import models, fields, api, _

class StockMove(models.Model):
    """
    Extends Stock Move to track secondary quantities throughout the movement lifecycle.
    """
    _inherit = 'stock.move'

    secondary_qty = fields.Float(
        string="Secondary Qty", 
        digits='Product Unit of Measure', 
        compute='_compute_secondary_qty', 
        store=True, 
        readonly=False,
        help="Initial secondary quantity to be moved."
    )
    secondary_qty_done = fields.Float(
        string="Secondary Qty Done",
        digits='Product Unit of Measure',
        compute='_compute_secondary_qty_done',
        inverse='_inverse_secondary_qty_done',
        store=True,
        readonly=False,
        help="Actual secondary quantity moved/processed."
    )
    secondary_uom_id = fields.Many2one(
        related='product_id.secondary_uom_id', 
        string="Secondary UoM", 
        readonly=True,
        help="Secondary unit of measure defined on the product."
    )

    @api.depends('product_uom_qty', 'product_id', 'product_id.secondary_uom_ratio')
    def _compute_secondary_qty(self):
        """ Computes initial secondary quantity for the move. """
        for move in self:
            if move.product_id.enable_secondary_uom:
                move.secondary_qty = move.product_id.convert_to_secondary(move.product_uom_qty)
            else:
                move.secondary_qty = 0.0

    @api.depends('quantity', 'product_id', 'product_id.secondary_uom_ratio')
    def _compute_secondary_qty_done(self):
        """ Computes processed secondary quantity. """
        for move in self:
            if move.product_id.enable_secondary_uom:
                move.secondary_qty_done = move.product_id.convert_to_secondary(move.quantity)
            else:
                move.secondary_qty_done = 0.0

    def _inverse_secondary_qty_done(self):
        """ Syncs primary quantity when secondary done quantity is edited. """
        for move in self:
            if move.product_id.enable_secondary_uom and move.product_id.secondary_uom_ratio:
                move.quantity = move.product_id.convert_to_primary(move.secondary_qty_done)

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """ Ensures secondary quantity is passed down to move lines (operations). """
        vals = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self.product_id.enable_secondary_uom:
            qty = quantity or self.product_uom_qty
            vals['secondary_qty_done'] = self.product_id.convert_to_secondary(qty)
        return vals

class StockMoveLine(models.Model):
    """
    Extends Stock Move Line (Operations) to support secondary quantities.
    """
    _inherit = 'stock.move.line'

    secondary_qty_done = fields.Float(
        string="Secondary Qty Done", 
        digits='Product Unit of Measure', 
        compute='_compute_secondary_qty_done', 
        inverse='_inverse_secondary_qty_done', 
        store=True, 
        readonly=False,
        help="Secondary quantity processed at the line level."
    )
    secondary_uom_id = fields.Many2one(
        related='product_id.secondary_uom_id',
        string="Secondary UoM",
        readonly=True
    )

    @api.depends('quantity', 'product_id', 'product_id.secondary_uom_ratio')
    def _compute_secondary_qty_done(self):
        """ Computes processed secondary quantity at the line level. """
        for line in self:
            if line.product_id.enable_secondary_uom:
                line.secondary_qty_done = line.product_id.convert_to_secondary(line.quantity)
            else:
                line.secondary_qty_done = 0.0

    def _inverse_secondary_qty_done(self):
        """ Syncs primary quantity at the line level. """
        for line in self:
            if line.product_id.enable_secondary_uom and line.product_id.secondary_uom_ratio:
                line.quantity = line.product_id.convert_to_primary(line.secondary_qty_done)

class StockQuant(models.Model):
    """
    Extends Stock Quant (Inventory Levels) to display stock in secondary units.
    """
    _inherit = 'stock.quant'

    secondary_quantity = fields.Float(
        string="Secondary Quantity", 
        digits='Product Unit of Measure', 
        compute='_compute_secondary_quantity', 
        store=True,
        help="Current stock level expressed in secondary unit of measure."
    )
    secondary_uom_id = fields.Many2one(
        related='product_id.secondary_uom_id',
        string="Secondary UoM",
        readonly=True
    )

    @api.depends('quantity', 'product_id', 'product_id.secondary_uom_ratio')
    def _compute_secondary_quantity(self):
        """ Computes inventory levels in secondary units. """
        for quant in self:
            if quant.product_id.enable_secondary_uom:
                quant.secondary_quantity = quant.product_id.convert_to_secondary(quant.quantity)
            else:
                quant.secondary_quantity = 0.0

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity=False, reserved_quantity=False, lot_id=None, package_id=None, owner_id=None, in_date=None):
        """ 
        Overrides to ensure quant update triggers if necessary, 
        though @api.depends usually handles stored compute fields automatically.
        """
        res = super()._update_available_quantity(
            product_id, location_id, quantity=quantity, reserved_quantity=reserved_quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id, in_date=in_date
        )
        return res
