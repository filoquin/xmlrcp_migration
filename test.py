from odoo_xmlrcp_migration import odoo_xmlrcp_migration, res_country_method


plan = odoo_xmlrcp_migration()
# plan.save_plan('res.partner')
# plan.save_plan('res.partner.category')
# plan.migrate('res.partner.category')
#plan.migrate('res.country.state')

plan.migrate('res.partner')

# plan.domain = [('id', '>', 134383), ]
# plan.migrate('res.partner')