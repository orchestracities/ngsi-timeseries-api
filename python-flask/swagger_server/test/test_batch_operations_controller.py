# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.batch_operation import BatchOperation  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.models.query import Query  # noqa: E501
from swagger_server.test import BaseTestCase


class TestBatchOperationsController(BaseTestCase):
    """BatchOperationsController integration test stubs"""

    def test_query(self):
        """Test case for query

        
        """
        body = Query()
        query_string = [('limit', 1.2),
                        ('offset', 1.2),
                        ('orderBy', 'orderBy_example'),
                        ('options', 'options_example')]
        response = self.client.open(
            '/context/v2/op/query',
            method='POST',
            data=json.dumps(body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update(self):
        """Test case for update

        
        """
        body = BatchOperation()
        query_string = [('options', 'options_example')]
        response = self.client.open(
            '/context/v2/op/update',
            method='POST',
            data=json.dumps(body),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
