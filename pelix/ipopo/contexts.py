#!/usr/bin/env python
# -- Content-Encoding: UTF-8 --
"""
Definition of Factory and Component context classes

:author: Thomas Calmant
:copyright: Copyright 2013, isandlaTech
:license: GPLv3
:version: 0.5.5
:status: Alpha

..

    This file is part of iPOPO.

    iPOPO is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    iPOPO is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with iPOPO. If not, see <http://www.gnu.org/licenses/>.
"""

# Module version
__version_info__ = (0, 5, 5)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"

# ------------------------------------------------------------------------------

# Pelix beans
from pelix.framework import BundleContext

# Pelix utilities
from pelix.constants import OBJECTCLASS
from pelix.utilities import is_string
import pelix.ldapfilter as ldapfilter

# iPOPO constants
import pelix.ipopo.constants as constants

# Standard library
import copy

# ------------------------------------------------------------------------------

class Requirement(object):
    """
    Represents a component requirement
    """
    # The dictionary form fields (filter is a special case)
    __stored_fields__ = ('specification', 'aggregate', 'optional')

    def __init__(self, specification, aggregate=False, optional=False,
                 spec_filter=None):
        """
        Sets up the requirement

        :param specification: The requirement specification, which must be
                              unique and can't be None
        :param aggregate: If true, this requirement represents a list
        :param optional: If true, this requirement is optional
        :param spec_filter: A filter to select dependencies

        :raise TypeError: A parameter has an invalid type
        :raise ValueError: An error occurred while parsing the filter
        """
        if not is_string(specification):
            raise TypeError("A Requirement specification must be a string")

        if not specification:
            raise ValueError("No specification given")

        self.specification = specification
        self.aggregate = aggregate
        self.optional = optional

        # Original filter keeper
        self.__original_filter = None

        # Full filter (with the specification test)
        self.__full_filter = None

        # Set up the requirement filter (after setting up self.specification)
        self.filter = None
        self.set_filter(spec_filter)


    def __eq__(self, other):
        """
        Equality test
        """
        if other is self:
            # Identity check
            return True

        if not isinstance(other, Requirement):
            # Different types
            return False

        if self.aggregate != other.aggregate or self.optional != other.optional:
            # Different flags
            return False

        if self.specification != other.specification:
            # Different specifications
            return False

        if self.filter != other.filter:
            # Different filters (therefore different specifications)
            return False

        return True


    def __ne__(self, other):
        """
        Inequality test
        """
        return not self.__eq__(other)


    def __deepcopy__(self, memo):
        """
        Called by copy.deepcopy()
        """
        return self.copy()


    def copy(self):
        """
        Returns a copy of this instance

        :return: A copy of this instance
        """
        return Requirement(self.specification, self.aggregate, self.optional,
                           self.__original_filter)


    def matches(self, properties):
        """
        Tests if the given _StoredInstance matches this requirement

        :param properties: Service properties
        :return: True if the instance matches this requirement
        """
        if properties is None:
            # No properties : invalid service
            return False

        # Properties filter test
        return self.__full_filter.matches(properties)


    @property
    def full_filter(self):
        """
        The filter that tests both specification and properties
        """
        return self.__full_filter


    @property
    def original_filter(self):
        """
        The original requirement filter string, not the computed one
        """
        if self.__original_filter is None:
            return ""

        return str(self.__original_filter)


    def set_filter(self, props_filter):
        """
        Changes the current filter for the given one

        :param props_filter: The new requirement filter on service properties
        :raise TypeError: Unknown filter type
        """
        if props_filter is not None \
        and not (is_string(props_filter) \
                 or isinstance(props_filter, (ldapfilter.LDAPFilter,
                                              ldapfilter.LDAPCriteria))):
            # Unknown type
            raise TypeError("Invalid filter type {0}" \
                            .format(type(props_filter).__name__))

        if props_filter is not None:
            # Filter given, keep its string form
            self.__original_filter = str(props_filter)
        else:
            # No filter
            self.__original_filter = None

        # Parse the filter
        self.filter = ldapfilter.get_ldap_filter(props_filter)

        # Prepare the full filter
        spec_filter = "({0}={1})".format(OBJECTCLASS, self.specification)
        self.__full_filter = ldapfilter.combine_filters((spec_filter,
                                                         self.filter))

# ------------------------------------------------------------------------------

class FactoryContext(object):
    """
    Represents the data stored in a component factory (class)
    """
    def __init__(self):
        """
        Sets up the factory context
        """
        # Factory bundle context
        self.bundle_context = None

        # Callbacks : Kind -> callback method
        self.callbacks = {}

        # Field callbacks: Field -> {Kind -> Callback}
        self.field_callbacks = {}

        # The factory name
        self.name = None

        # Properties : Name -> Value
        self.properties = {}

        # Properties fields : Field name -> Property name
        self.properties_fields = {}

        # The factory manipulation has been completed
        self.completed = False

        # Handler ID -> configuration
        self.__handlers = {}


    def __eq__(self, other):
        """
        Equality test
        """
        if other is self:
            # Identity
            return True

        if not isinstance(other, FactoryContext):
            # Different types
            return False

        # Name-based equality
        return self.name == other.name


    def __ne__(self, other):
        """
        Inequality test
        """
        return not self.__eq__(other)


    def get_handlers_ids(self):
        """
        Retrieves the IDs of the handlers to instantiate for this component
        """
        return list(self.__handlers.keys())


    def copy(self):
        """
        Returns a deep copy of the current FactoryContext instance
        """
        return copy.deepcopy(self)


    def get_handler(self, handler_id, default=None):
        """
        Retrieves the configuration associated to the given handler

        :param handler_id: The ID of the configured handler
        :param default: The default configuration value
        :return: The existing configuration or the given default
        """
        return self.__handlers.setdefault(handler_id, default)


    def set_handler(self, handler_id, configuration):
        """
        Stores the configuration of the given handler

        :param handler_id: The ID of the configured handler
        :param configuration: The complete configuration of the handler
        """
        self.__handlers[handler_id] = configuration


    def set_bundle_context(self, bundle_context):
        """
        Sets up the bundle context associated to this factory context

        :param bundle_context: The factory bundle context
        """
        if self.bundle_context is None:
            assert isinstance(bundle_context, BundleContext)
            self.bundle_context = bundle_context

# ------------------------------------------------------------------------------

class ComponentContext(object):
    """
    Represents the data stored in a component instance
    """
    # Try to reduce memory footprint (many instances)
    __slots__ = ('factory_context', 'name', 'properties')

    def __init__(self, factory_context, name, properties):
        """
        Sets up the context

        :param factory_context: The parent factory context
        :param properties: The component properties
        """
        assert isinstance(factory_context, FactoryContext)
        assert isinstance(properties, dict)

        self.factory_context = factory_context
        self.name = name

        # Force the instance name property
        properties[constants.IPOPO_INSTANCE_NAME] = name

        self.properties = factory_context.properties.copy()
        self.properties.update(properties)


    def get_bundle_context(self):
        """
        Retrieves the bundle context

        :return: The component bundle context
        """
        return self.factory_context.bundle_context


    def get_callback(self, event):
        """
        Retrieves the registered method for the given event. Returns None if not
        found

        :param event: A component life cycle event
        :return: The callback associated to the given event
        """
        return self.factory_context.callbacks.get(event, None)


    def get_field_callback(self, field, event):
        """
        Retrieves the registered method for the given event. Returns None if not
        found

        :param field: Name of the dependency field
        :param event: A component life cycle event
        :return: The callback associated to the given event
        """
        return self.factory_context.field_callbacks.get(field,
                                                        {}).get(event, None)


    def get_factory_name(self):
        """
        Retrieves the component factory name

        :return: The component factory name
        """
        return self.factory_context.name


    def get_handler(self, handler_id):
        """
        Retrieves the configuration for the given handler from the factory
        context

        :param handler_id: The ID of the configured handler
        :return: The handler configuration, or None
        """
        return self.factory_context.get_handler(handler_id, None)
