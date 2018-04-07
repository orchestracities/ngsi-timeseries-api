# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.entity import Entity  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestAttributesController(BaseTestCase):
    """AttributesController integration test stubs"""

    def test_get_attribute_data(self):
        """Test case for get_attribute_data

        
        """
        query_string = [('type', 'type_example')]
        response = self.client.open(
            '/v2/entities/{entityId}/attrs/{attrName}'.format(entityId='entityId_example', attrName='attrName_example'),
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_a_single_attribute(self):
        """Test case for remove_a_single_attribute

        
        """
        query_string = [('type', 'type_example')]
        response = self.client.open(
            '/v2/entities/{entityId}/attrs/{attrName}'.format(entityId='entityId_example', attrName='attrName_example'),
            method='DELETE',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_attribute_data(self):
        """Test case for update_attribute_data

        
        """
        body = None
        query_string = [('type', 'type_example')]
        response = self.client.open(
            '/v2/entities/{entityId}/attrs/{attrName}'.format(entityId='entityId_example', attrName='attrName_example'),
            method='PUT',
            data=json.dumps(body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
