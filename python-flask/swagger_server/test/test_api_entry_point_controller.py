# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.api_entry_point import APIEntryPoint  # noqa: E501
from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestAPIEntryPointController(BaseTestCase):
    """APIEntryPointController integration test stubs"""

    def test_retrieve_api_resources(self):
        """Test case for retrieve_api_resources

        
        """
        response = self.client.open(
            '/v2/',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
