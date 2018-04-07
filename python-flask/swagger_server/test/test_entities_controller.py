# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.attribute import Attribute  # noqa: E501
from swagger_server.models.entity import Entity  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestEntitiesController(BaseTestCase):
    """EntitiesController integration test stubs"""

    def test_create_entity(self):
        """Test case for create_entity

        
        """
        body = Entity()
        query_string = [('options', 'options_example')]
        response = self.client.open(
            '/v2/entities',
            method='POST',
            data=json.dumps(body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_entities(self):
        """Test case for list_entities

        
        """
        query_string = [('id', 'id_example'),
                        ('type', 'type_example'),
                        ('idPattern', 'idPattern_example'),
                        ('typePattern', 'typePattern_example'),
                        ('q', 'q_example'),
                        ('mq', 'mq_example'),
                        ('georel', 'georel_example'),
                        ('geometry', 'geometry_example'),
                        ('coords', 'coords_example'),
                        ('limit', 1.2),
                        ('offset', 1.2),
                        ('attrs', 'attrs_example'),
                        ('orderBy', 'orderBy_example'),
                        ('options', 'options_example')]
        response = self.client.open(
            '/v2/entities',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_remove_entity(self):
        """Test case for remove_entity

        
        """
        query_string = [('type', 'type_example')]
        response = self.client.open(
            '/v2/entities/{entityId}'.format(entityId='entityId_example'),
            method='DELETE',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_replace_all_entity_attributes(self):
        """Test case for replace_all_entity_attributes

        
        """
        body = Attribute()
        query_string = [('type', 'type_example'),
                        ('options', 'options_example')]
        response = self.client.open(
            '/v2/entities/{entityId}/attrs'.format(entityId='entityId_example'),
            method='PUT',
            data=json.dumps(body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_retrieve_entity(self):
        """Test case for retrieve_entity

        
        """
        query_string = [('type', 'type_example'),
                        ('attrs', 'attrs_example'),
                        ('options', 'options_example')]
        response = self.client.open(
            '/v2/entities/{entityId}'.format(entityId='entityId_example'),
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_retrieve_entity_attributes(self):
        """Test case for retrieve_entity_attributes

        
        """
        query_string = [('type', 'type_example'),
                        ('attrs', 'attrs_example'),
                        ('options', 'options_example')]
        response = self.client.open(
            '/v2/entities/{entityId}/attrs'.format(entityId='entityId_example'),
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_existing_entity_attributes(self):
        """Test case for update_existing_entity_attributes

        
        """
        body = Attribute()
        query_string = [('type', 'type_example'),
                        ('options', 'options_example')]
        response = self.client.open(
            '/v2/entities/{entityId}/attrs'.format(entityId='entityId_example'),
            method='PATCH',
            data=json.dumps(body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_or_append_entity_attributes(self):
        """Test case for update_or_append_entity_attributes

        
        """
        body = Attribute()
        query_string = [('type', 'type_example'),
                        ('options', 'options_example')]
        response = self.client.open(
            '/v2/entities/{entityId}/attrs'.format(entityId='entityId_example'),
            method='POST',
            data=json.dumps(body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
