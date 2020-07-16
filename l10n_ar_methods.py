from odoo_xmlrcp_migration import odoo_xmlrcp_migration
import re


def validar_cuit(cuit):
    # based on http://www.python.org.ar/wiki/Recetario/ValidarCuit
    # devuelvo cuit o None si esinvalido
    # validaciones minimas
    cuit = cuit.replace('-', '')
    if len(cuit) != 11:
        return None

    base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    # calculo el digito verificador:
    aux = 0
    for i in xrange(10):
        aux += int(cuit[i]) * base[i]

    aux = 11 - (aux - (int(aux / 11) * 11))

    if aux == 11:
        aux = 0
    if aux == 10:
        aux = 9

    if aux == int(cuit[10]):
        return cuit
    else:
        return None


def map_document_number(self, value, field, plan, row, field_collection='fields'):
    if row['document_type_id'] and row['document_type_id'][1] == 'CUIT' and value:
        return validar_cuit(value)
    elif row['document_type_id'] and row['document_type_id'][1] == 'DNI' and value:
        return re.sub('[^0-9]', '', value)[:8].zfill(7)
    return value


# def __init__(self):
#    setattr(odoo_xmlrcp_migration, 'map_document_number', map_document_number)
setattr(odoo_xmlrcp_migration, 'map_document_number', map_document_number)
