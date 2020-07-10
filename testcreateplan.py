from odoo_xmlrcp_migration import odoo_xmlrcp_migration


plan = odoo_xmlrcp_migration()
# plan.save_plan('res.partner')
plan.save_plan('res.partner.category')
#plan.migrate('res.partner.category')
# plan.domain = [('id', '>', 134383), ]
#plan.migrate('res.partner', row_ids=[57133])
#plan.migrate('res.partner')