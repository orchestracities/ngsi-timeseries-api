# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.entity_type import EntityType  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestTypesController(BaseTestCase):
    """TypesController integration test stubs"""

    def test_retrieve_entity_type(self):
        """Test case for retrieve_entity_type

        
        """
        response = self.client.open(
            '/context/v2/types/{entityType}'.format(entityType='entityType_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_retrieve_entity_types(self):
        """Test case for retrieve_entity_types

        
        """
        query_string = [('limit', 1.2),
                        ('offset', 1.2),
                        ('options', 'options_example')]
        response = self.client.open(
            '/context/v2/types/',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
