# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.error_response import ErrorResponse  # noqa: E501
from swagger_server.models.subscription import Subscription  # noqa: E501
from swagger_server.test import BaseTestCase


class TestSubscriptionsController(BaseTestCase):
    """SubscriptionsController integration test stubs"""

    def test_create_a_new_subscription(self):
        """Test case for create_a_new_subscription

        
        """
        body = Subscription()
        response = self.client.open(
            '/context/v2/subscriptions',
            method='POST',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_delete_subscription(self):
        """Test case for delete_subscription

        
        """
        response = self.client.open(
            '/context/v2/subscriptions/{subscriptionId}'.format(subscriptionId='subscriptionId_example'),
            method='DELETE')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_retrieve_subscription(self):
        """Test case for retrieve_subscription

        
        """
        response = self.client.open(
            '/context/v2/subscriptions/{subscriptionId}'.format(subscriptionId='subscriptionId_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_retrieve_subscriptions(self):
        """Test case for retrieve_subscriptions

        
        """
        query_string = [('limit', 1.2),
                        ('offset', 1.2),
                        ('options', 'options_example')]
        response = self.client.open(
            '/context/v2/subscriptions',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_update_subscription(self):
        """Test case for update_subscription

        
        """
        body = Subscription()
        response = self.client.open(
            '/context/v2/subscriptions/{subscriptionId}'.format(subscriptionId='subscriptionId_example'),
            method='PATCH',
            data=json.dumps(body),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
