from odoo_xmlrcp_migration import odoo_xmlrcp_migration, mig_8_to_13
import l10n_ar_methods


plan = odoo_xmlrcp_migration()


plan.modules.append('l10n_ar')
plan.modules.append('city')
plan.modules.append('order_validity')

# plan.save_plan('res.partner')
# plan.save_plan('res.partner.category')
# plan.migrate('res.partner.category')
# plan.migrate('res.country.state')

# plan.migrate('res.partner', default_country_id=10)
# plan.domain = [('id', '>', 3), ]
# plan.migrate('res.users')

#order_ids = plan.migrate('sale.order')

#row_ids = order_ids['write']+order_ids['create']
plan.migrate('sale.order', row_ids=[225700], default_country_id=10)

print plan.cache['external_ids']
# plan.domain = [('id', '>', 134383), ]
# plan.migrate('res.partner')