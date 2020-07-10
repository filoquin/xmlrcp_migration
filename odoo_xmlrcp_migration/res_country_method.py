from . import odoo_xmlrcp_migration
from xmlrpc import client as xmlrpclib
import yaml


def res_country_map_external_id(self):
    server = self.socks['from']
    sock = server['sock']
    args = [('model', '=', 'res.country')]
    return sock.execute(
        server['dbname'],
        server['uid'],
        server['pwd'],
        'ir.model.data',
        'search_read',
        args,
        ['complete_name', 'res_id', 'name']
    )

setattr(odoo_xmlrcp_migration, 'res_country_map_external_id', res_country_map_external_id)
