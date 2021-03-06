# -*- coding: utf-8 -*-

"""
Entity classes
==============

The data model can be created manually if you wish to use separate property
names from the data keys, or define custom methods for your objects.

Custom entity
-------------

Define a base. These properties and methods are shared by all objects in the endpoint.

.. code-block:: python

    from odata.entity import declarative_base
    from odata.property import IntegerProperty, StringProperty, DatetimeProperty

    class MyBase(declaractive_base()):
        id = IntegerProperty('Id', primary_key=True)
        created_date = DatetimeProperty('Created')
        modified_date = DatetimeProperty('Modified')

        def did_somebody_touch_this(self):
            return self.created_date != self.modified_date

Define a model:

.. code-block:: python

    class Product(MyBase):
        __odata_type__ = 'ProductDataService.Objects.Product'
        __odata_collection__ = 'Products'

        name = StringProperty('ProductName')
        quantity_in_storage = IntegerProperty('QuantityInStorage')

        def is_product_available(self):
            return self.quantity_in_storage > 0

Note that the type (EntityType) and collection (EntitySet) must be defined.
These are used in querying and saving data.

Use the base to init :py:class:`~odata.service.ODataService`:

.. code-block:: python

    Service = ODataService(url, base=MyBase)

Unlike reflection, this does not require any network connections. Now you can
use the Product class to create new objects or query existing ones:

.. code-block:: python

    query = Service.query(Product)
    query = query.filter(Product.name.startswith('Kettle'))
    for product in query:
        print(product.name, product.is_product_available())
"""

try:
    # noinspection PyUnresolvedReferences
    from urllib.parse import urljoin
except ImportError:
    # noinspection PyUnresolvedReferences
    from urlparse import urljoin

from odata.state import EntityState


class EntityBase(object):
    __odata_url_base__ = ''
    __odata_collection__ = 'Entities'
    __odata_type__ = 'ODataSchema.Entity'

    @classmethod
    def __odata_url__(cls):
        # used by Query
        return urljoin(cls.__odata_url_base__, cls.__odata_collection__)

    def __new__(cls, *args, **kwargs):
        i = super(EntityBase, cls).__new__(cls)
        i.__odata__ = es = EntityState(i)

        if 'from_data' in kwargs:
            raw_data = kwargs.pop('from_data')

            # check for values from $expand
            for prop_name, prop in es.navigation_properties:
                if prop.name in raw_data:
                    expanded_data = raw_data.pop(prop.name)
                    if prop.is_collection:
                        es.nav_cache[prop.name] = dict(collection=prop.instances_from_data(expanded_data))
                    else:
                        es.nav_cache[prop.name] = dict(single=prop.instances_from_data(expanded_data))

            for prop_name, prop in es.properties:
                i.__odata__[prop.name] = raw_data.get(prop.name)
        else:
            for prop_name, prop in es.properties:
                i.__odata__[prop.name] = None

        return i

    def __repr__(self):
        clsname = self.__class__.__name__
        prop_name, prop = self.__odata__.primary_key_property
        if prop:
            value = self.__odata__[prop.name]
            if value:
                return '<Entity({0}:{1})>'.format(clsname, prop.escape_value(value))
        return '<Entity({0})>'.format(clsname)

    def __eq__(self, other):
        if isinstance(other, EntityBase):
            my_id = self.__odata__.id
            if my_id:
                return my_id == other.__odata__.id
        return False


def declarative_base():
    class Entity(EntityBase):
        pass
    return Entity
