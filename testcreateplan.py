from odoo_xmlrcp_migration import odoo_xmlrcp_migration


plan = odoo_xmlrcp_migration('/etc/odoo_xmlrcp_migration2.conf')
plan.save_plan('res.users')
plan.save_plan('res.partner')
plan.save_plan('sale.order')
plan.save_plan('sale.order.line')

plan.save_plan('product.product')
plan.save_plan('product.template')
plan.save_plan('product.pricelist')
plan.save_plan('crm.case.section', 'crm.team')
plan.save_plan('product.uom.categ', 'uom.category')
plan.save_plan('res.country')
plan.save_plan('res.country.state')
plan.save_plan('res.country.state.city', 'res.city')


#plan.save_plan('res.partner.category')
