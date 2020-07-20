# Migración de odoo en XMLRCP semi automatizada (poor man’s migration)

## ¿Porque?
El proceso de migración siempre es difícil. El trabajo de un upgrade de versión odoo debería centrarse en cómo el deploy, en organizamos los workflow, qué módulos instalamos. No en pasar datos.  

**Las instalaciones de odoo** son diferentes y muy customizadas. Hay módulos que salen o entran en el core (claim, city) o cambian de desarrollador (product pack).
El **openupgrade** podria solucionar una migración, pero muchos módulos no tienen soporte.
Migrar de 8 a 13 implicaría generar 5 instalaciones y escribir y verificar las 5 migraciones de todos los módulos no soportados. (por ejemplo múltiples localizaciones, product pack, etc) 

## ¿como funciona?
Migración recursiva basada en una librería que transfiere datos via XMLRCP y un plan de migración repetible, reutilizable y realizable en etapas. Las instrucciones de migración son archivos yaml y py.
Es recusiva porque el modelo sale.order tira de las lineas, las lineas tiran de los productos, y tambien de los partner, usuarios, equipos de ventas etc)


## Conceptos Base 
* **ir.model.access:** Modelo de odoo usado para machear los registros entre un odoo y otro. Utilizo el de la base destino.
* Plan de migración: Es un folder que engloba todos los archivos que describen la migración (yaml, py). podría haber un plan por cada versión de origen y destino(8_13, 11_13,etc)
* **Módulos:** Una subcarpeta por cada módulo migrado (no necesariamente coinciden con  los módulos de odoo)
* **Modelos:** Los modelos son archivos yaml que describen el modelo de origen y destino, campos a migrar (y sus respectivos nombres) como macheo los registros y como procesos los campos.
* **Guión:** Una serie de instrucciones que se ejecutan sobre la clase odoo_xmlrcp_migration . Uno por cada migración.

## Creación del plan.
Para iniciar un plan puedo usar la función 
```python
from odoo_xmlrcp_migration import odoo_xmlrcp_migration


plan = odoo_xmlrcp_migration('/etc/odoo_xmlrcp_migration2.conf')
plan.save_plan('res.partner')
```

## Ejecución de una migración.
Origen. mi instalación activa.
Destino: un odoo ya configurado sin datos. 
```python
from odoo_xmlrcp_migration import odoo_xmlrcp_migration
plan = odoo_xmlrcp_migration('/etc/odoo_xmlrcp_migration2.conf')

plan.test = True
plan.modules.append('l10n_ar')
plan.modules.append('city')
plan.modules.append('order_validity')
plan.migrate('sale.order')
```

## To-do:
* Cargar python de módulos de manera onfly con la carga de funciones python
* Módulo en odoo destino que me permita modificar los datos de auditoría de los registros y bloquee los mensajes de creación, etc en destino.
* Poder instalar con pip
* Mejoras en generación de plan
* Refactorizar código
* Invitar a la comunidad a crear planes y módulos



