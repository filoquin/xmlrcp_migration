from odoo_xmlrcp_migration import odoo_xmlrcp_migration
import l10n_ar_methods


plan = odoo_xmlrcp_migration()
plan.plan.append('l10n_ar')
plan.plan.append('city')
# plan.save_plan('res.partner')
# plan.save_plan('res.partner.category')
# plan.migrate('res.partner.category')
# plan.migrate('res.country.state')

plan.migrate('res.partner', default_country_id=10)
print plan.cache['external_ids']
# plan.domain = [('id', '>', 134383), ]
# plan.migrate('res.partner')