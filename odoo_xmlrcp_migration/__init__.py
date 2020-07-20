from configparser import ConfigParser
from xmlrpc import client as xmlrpclib
import yaml
import os


class odoo_xmlrcp_migration(object):
    socks = {}
    modules = ['base']
    domain = []
    chunk_size = 100
    is_test = False
    cache = {'plans': {}, 'external_ids': {}}
    system_fields = ['id', 'write_date', 'write_uid', 'create_date', 'create_uid', '__last_update']

    def __init__(self, config_file='/etc/odoo_xmlrcp_migration.conf'):
        self.config = ConfigParser()
        self.config.read(config_file)
        self.data_dir = self.config.get("yalm", 'path')
        self.socks['from'] = {
            'dbname': self.config.get("odooserver_1", 'dbname'),
            'username': self.config.get("odooserver_1", 'username'),
            'pwd': self.config.get("odooserver_1", 'pwd'),
            'url': self.config.get("odooserver_1", 'url'),
        }
        self.socks['from']['sock_common'] = xmlrpclib.ServerProxy(self.socks['from']['url'] + 'xmlrpc/common')

        self.socks['from']['uid'] = self.socks['from']['sock_common'].login(
            self.socks['from']['dbname'],
            self.socks['from']['username'],
            self.socks['from']['pwd']
        )
        self.socks['from']['sock'] = xmlrpclib.ServerProxy(self.socks['from']['url'] + 'xmlrpc/object')

        self.socks['to'] = {
            'dbname': self.config.get("odooserver_2", 'dbname'),
            'username': self.config.get("odooserver_2", 'username'),
            'pwd': self.config.get("odooserver_2", 'pwd'),
            'url': self.config.get("odooserver_2", 'url'),
        }
        self.socks['to']['sock_common'] = xmlrpclib.ServerProxy(self.socks['to']['url'] + 'xmlrpc/common')

        self.socks['to']['uid'] = self.socks['to']['sock_common'].login(
            self.socks['to']['dbname'],
            self.socks['to']['username'],
            self.socks['to']['pwd']
        )
        self.socks['to']['sock'] = xmlrpclib.ServerProxy(self.socks['to']['url'] + 'xmlrpc/object')

    def clean_cache(self):
        self.cache = {'plans': {}, 'external_ids': {}}

    def xfields_get(self, server, model):
        server = self.socks[server]
        sock = server['sock']
        return sock.execute(server['dbname'], server['uid'], server['pwd'], model, 'fields_get')

    def fields_get(self, server, model, ignore_readonly=False):
        server = self.socks[server]
        sock = server['sock']
        leaf = [('model_id.model', '=', model), ('name', 'not in', self.system_fields)]
        if ignore_readonly:
            leaf += [('readonly', '=', False)]
        f = sock.execute(
            server['dbname'],
            server['uid'],
            server['pwd'],
            'ir.model.fields',
            'search_read',
            leaf, []
        )

        return {x['name']: x for x in f}

    def compare_model(self, model_from, model_to=False):
        fields = {}
        no_match_fields = {}
        model_to = model_to if model_to else model_from
        fields_from = self.fields_get('from', model_from)
        fields_to = self.fields_get('to', model_to, True)
        keys_from = set(fields_from.keys())
        keys_to = set(fields_to.keys())
        intersection = keys_from & keys_to
        for field in list(intersection):
            if fields_from[field]['modules'] not in fields:
                # to-do: defaultdict ?
                fields[fields_from[field]['modules']] = {}
            # if not fields_to[field].get('store', True):
            #    continue
            fields[fields_from[field]['modules']][field] = self.dump_config_field(field, fields_from, fields_to)
        diff = keys_from - keys_to
        for field in list(diff):

            if fields_from[field]['modules'] not in no_match_fields:
                # to-do: defaultdict ?
                no_match_fields[fields_from[field]['modules']] = {}
            # if not fields_to[field].get('store', True):
            #    continue
            no_match_fields[fields_from[field]['modules']][field] = self.dump_config_field(field, fields_from, fields_to)

        return fields, no_match_fields

    def dump_config_field(self, field, fields_from, fields_to):
        field_temp = {}
        if field in fields_from:
            field_temp['from'] = {'name': field, 'type': fields_from[field]['ttype']}
            if fields_from[field]['relation']:
                field_temp['from']['relation'] = fields_from[field]['relation']
            if fields_from[field]['relation_field']:
                field_temp['from']['relation_field'] = fields_from[field]['relation_field']

        if field in fields_to:
            field_temp['to'] = {'name': field, 'type': fields_to[field]['ttype']}

            if fields_to[field]['relation']:
                field_temp['to']['relation'] = fields_to[field]['relation']
            if fields_to[field]['relation_field']:
                field_temp['to']['relation_field'] = fields_to[field]['relation_field']
        if field in fields_to and field in fields_from:
            if fields_to[field]['ttype'] == fields_to[field]['ttype']:
                field_temp['map_method'] = 'magic_map'
            else:
                field_temp['map_method'] = '%s2%s' % (fields_from[field]['ttype'] == fields_from[field]['ttype'])
        return field_temp

    def ensure_dir(self, file_path):
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def save_plan(self, model_from, model_to=False, ignore_module=False):
        model_to = model_to if model_to else model_from
        data = {}
        data['model_from'] = model_from
        data['model_to'] = model_to
        data['domain'] = []
        data['external_id_nomenclature'] = model_from.replace('.', '_') + "_%s"
        data['external_id_method'] = 'row_get_id'
        fields_by_module, no_match_fields = self.compare_model(model_from, model_to)
        model_name = model_from.replace('.', '_')
        for module in fields_by_module:
            data['fields'] = fields_by_module[module] if module in fields_by_module else []
            data['no_match_fields'] = no_match_fields[module] if module in no_match_fields else []
            file_name = '%s/%s/%s.yaml' % (self.data_dir, module, model_name)
            self.ensure_dir(file_name)
            with open(file_name, 'w+') as file:
                yaml.dump(data, file)

    def load_plan(self, model_from):
        model_name = model_from.replace('.', '_')
        if model_name in self.cache['plans']:
            return self.cache['plans'][model_name]
        result = {}

        for module in self.modules:
            try:
                with open('%s/%s/%s.yaml' % (self.data_dir, module, model_name)) as file:
                    data = yaml.full_load(file)
                    if not len(result):
                        result = data
                    else:
                        result['fields'].update(data['fields'])
                        result['domain'] += data['domain']
            except IOError:
                pass
        if len(result) == 0:
            print ("Not exists plan for %s" % model_from)
        self.cache['plans'][model_name] = result
        return result

    def get_context(self, **kwargs):
        return kwargs['context'] if 'context' in kwargs else {}

    def migrate(self, model_name, **kwargs):
        plan = self.load_plan(model_name)
        res_ids = {'create': [], 'write': []}
        field_names = plan['fields'].keys()
        after_save_fields = plan['after_save_fields'].keys() if 'after_save_fields' in plan else []
        if 'ignore_field' in kwargs and kwargs['ignore_field'] in field_names:
            print "remuevo %s de %s " % (kwargs['ignore_field'], model_name)
            field_names.remove(kwargs['ignore_field'])

        if 'row_ids' in kwargs:
            row_ids = kwargs['row_ids']
        else:
            model_domain = kwargs['domain'] if 'domain' in kwargs else []
            row_ids = self.get_ids(plan['model_from'], plan['domain'] + model_domain + self.domain)
        chunk = [row_ids[i:i + self.chunk_size] for i in xrange(0, len(row_ids), self.chunk_size)]
        for ids in chunk:
            rows = self.read(plan['model_from'], ids, field_names + after_save_fields)
            for row in rows:
                data = self.map_data(plan, row, kwargs)
                action, model, res_id = self.save(plan, data, row['id'])
                res_ids[action].append(res_id)
                if len(after_save_fields):
                    data = self.map_data(plan, row, kwargs, 'after_save_fields')
                    self.save(plan, data, row['id'])

            if self.is_test:
                return res_ids
        return res_ids

    def save(self, plan, values, orig_id):
        external_id_method = getattr(self, plan['external_id_method'])
        ext_id = external_id_method(plan, orig_id, plan['external_id_nomenclature'])
        server = self.socks['to']
        sock = server['sock']
        if len(ext_id):
            try:

                sock.execute(
                    server['dbname'],
                    server['uid'],
                    server['pwd'],
                    plan['model_to'],
                    'write',
                    [ext_id[0]['res_id']],
                    values
                )
                print ('write %s %s' % (plan['model_to'], ext_id[0]['res_id']))
                return ('write', plan['model_to'], ext_id)
            except xmlrpclib.Fault, e:
                print (e.faultCode)
                return ('write', plan['model_to'], False)

        else:
            try:
                res_id = sock.execute(
                    server['dbname'],
                    server['uid'],
                    server['pwd'],
                    plan['model_to'],
                    'create',
                    [values]
                )
                print ('create %s %s' % (plan['model_to'], res_id[0]))
                self.add_external_id(plan['model_to'], orig_id, res_id[0], plan['external_id_nomenclature'])
                return ('create', plan['model_to'], res_id[0])
            except xmlrpclib.Fault, e:
                print (e.faultCode)
                return ('create', plan['model_to'], False)

    def get_ids(self, model, domain):
        server = self.socks['from']
        sock = server['sock']
        return sock.execute(server['dbname'], server['uid'], server['pwd'], model, 'search', domain)

    def read(self, model, ids, fields):
        server = self.socks['from']
        sock = server['sock']
        return sock.execute(
            server['dbname'],
            server['uid'],
            server['pwd'],
            model,
            'read',
            ids,
            fields
        )

    def get_default(self, field, kwargs):
        return kwargs.get('default_%s' % field, None)

    def map_data(self, plan, row, kwargs, field_collection='fields'):
        maping = {}
        for field in plan[field_collection]:
            f = plan[field_collection][field]
            if f['from']['name'] not in row:
                continue
            map_method = getattr(self, f['map_method'] if 'map_method' in f else 'magic_map')
            val = map_method(row[f['from']['name']], field, plan, row,field_collection)
            default_value = self.get_default(field, kwargs)
            if val is not None or default_value is not None:
                maping[f['to']['name']] = val if val is not None else default_value
        return maping

    def magic_map(self, value, field, plan, row, field_collection='fields'):
        field_data = plan[field_collection][field]
        if field_data['from']['type'] in ['selection', 'date', 'datetime',
                                          'char', 'float', 'integer',
                                          'text', 'html', 'boolean']:
            # to-do : Cast Value type
            return value
        elif field_data['from']['type'] == 'one2many':
            subplan = self.load_plan(field_data['from']['relation'])
            if not subplan:
                return None
            external_id_method = getattr(self, subplan['external_id_method'])
            res_ids = []
            for res_id in value:
                ext_id = external_id_method(subplan, res_id, row)
                if len(ext_id):
                    res_ids.append(ext_id[0]['res_id'])
                else:
                    if field_data.get('required', False):
                        ignore_field = field_data['from']['relation_field']
                    else:
                        ignore_field = False
                    new = self.migrate(
                        field_data['from']['relation'],
                        row_ids=[res_id],
                        ignore_field=ignore_field

                    )
                    res_ids.append(new['create'][0])
            return [(6, 0, res_ids)]

        elif field_data['from']['type'] in ['many2one'] and value:
            subplan = self.load_plan(field_data['from']['relation'])
            if len(subplan) == 0:
                return None
            external_id_method = getattr(self, subplan['external_id_method'])
            ext_id = external_id_method(subplan, value[0], row, field_data.get('cache', False))
            if len(ext_id):
                return ext_id[0]['res_id']
            else:
                new = self.migrate(
                    field_data['from']['relation'],
                    row_ids=[value[0]]
                )
                return new['create'][0]
        elif field_data['from']['type'] in ['many2many']:
            subplan = self.load_plan(field_data['from']['relation'])
            if not subplan:
                return None
            external_id_method = getattr(self, subplan['external_id_method'])
            res_ids = []
            for res_id in value:
                ext_id = external_id_method(subplan, res_id, row)
                if len(ext_id):
                    res_ids.append(ext_id[0]['res_id'])
                else:
                    new = self.migrate(
                        field_data['from']['relation'],
                        row_ids=[res_id]
                    )
                    res_ids.append(new['create'][0])
            return [(6, 0, res_ids)]

        return None

    def row_get_id(self, plan, value, row, cache=False):
        server = self.socks['to']
        sock = server['sock']
        nomeclature = plan['external_id_nomenclature']
        args = [('name', '=', nomeclature % value),
                ('module', '=', 'xmlrpc_migration'),
                ('model', '=', plan['model_to'])]

        res = sock.execute(
            server['dbname'],
            server['uid'],
            server['pwd'],
            'ir.model.data',
            'search_read',
            args,
            ['res_id']
        )

        if cache and len(res):
            if plan['model_from'] not in self.cache['external_ids']:
                self.cache['external_ids'][plan['model_from']] = {}
            self.cache['external_ids'][plan['model_from']][value] = res[0]['res_id']

        return res

    def add_external_id(self, model, orig_id, dest_id, nomeclature):
        server = self.socks['to']
        sock = server['sock']
        vals = [{
                'name': nomeclature % orig_id,
                'module': 'xmlrpc_migration',
                'model': model,
                'res_id': dest_id,
                'noupdate': True
                }]

        return sock.execute(
            server['dbname'],
            server['uid'],
            server['pwd'],
            'ir.model.data',
            'create',
            vals
        )

    def same_external_id(self, plan, res_id, row, cache=False):
        server = self.socks['from']
        sock = server['sock']
        external_id = sock.execute(
            server['dbname'],
            server['uid'],
            server['pwd'],
            'ir.model.data',
            'search_read',
            [('res_id', '=', res_id), ('model', '=', plan['model_from'])],
            ['complete_name', 'res_id', 'name']
        )
        if len(external_id):
            server = self.socks['to']
            sock = server['sock']
            res = sock.execute(
                server['dbname'],
                server['uid'],
                server['pwd'],
                'ir.model.data',
                'search_read',
                [('name', '=', external_id[0]['name']), ('model', '=', plan['model_to'])],
                ['res_id']
            )
            if cache:
                if plan['model_from'] not in self.cache['external_ids']:
                    self.cache['external_ids'][plan['model_from']] = {}
                self.cache['external_ids'][plan['model_from']][res_id] = res[0]['res_id']
            return res

        return None

    def match_field(self, plan, res_id, row, cache=False):
        server = self.socks['from']
        sock = server['sock']
        external_field_value = sock.execute(
            server['dbname'],
            server['uid'],
            server['pwd'],
            plan['model_from'],
            'read',
            [res_id],
            [plan['external_id_field_from']]
        )
        if len(external_field_value):

            server = self.socks['to']
            sock = server['sock']
            external_id = sock.execute(
                server['dbname'],
                server['uid'],
                server['pwd'],
                plan['model_to'],
                'search',
                [(plan['external_id_field_to'], '=', external_field_value[0][plan['external_id_field_from']])]
            )
            if len(external_id):
                if cache:
                    if plan['model_from'] not in self.cache['external_ids']:
                        self.cache['external_ids'][plan['model_from']] = {}
                    self.cache['external_ids'][plan['model_from']][res_id] = external_id[0]

                return [{'res_id': external_id[0]}]
        return None
