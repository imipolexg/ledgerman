#!/usr/bin/env python
import __builtin__
__builtin__.ledgerman_testing = True
import unittest
import falcon
import falcon.testing as testing
import faker
import ledgerman
import json

fake = faker.Factory.create()


class LedgermanTest(testing.TestCase):
    headers = {
        'X-API-Token': ledgerman.APITokenMiddleware.gen_api_token(),
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json'
    }

    def setUp(self):
        super(LedgermanTest, self).setUp()

        self.api = ledgerman.api


class PlayerResourceTest(LedgermanTest):
    """Basic CRUD functionality tests, no testing of edge cases."""

    def test_crud(self):
        for i in range(50):
            playerObj = {
                'type': 'player',
                'attributes': {
                    'email': fake.email(),
                    'name': fake.name(),
                    'handle': fake.word(),
                    'avatar-url': fake.uri()
                }
            }

            jsonObj = json.dumps(playerObj)

            headers = self.headers.copy()
            headers['Content-Length'] = str(len(jsonObj))

            # test create
            result = self.simulate_post('/players', headers=headers, body=jsonObj)
            self.assertEqual(result.status_code, 200)

            newResObj = result.json
            playerObj['id'] = newResObj['id']

            self.assertEqual(playerObj, newResObj)

            # Test read
            del headers['Content-Length']
            result = self.simulate_get('/players/{0}'.format(newResObj['id']), headers=headers)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(newResObj, result.json)

            # Test update
            playerObj['attributes']['email'] = fake.email()
            jsonObj = json.dumps(playerObj)
            headers['Content-Length'] = str(len(jsonObj))

            result = self.simulate_patch('/players/{0}'.format(playerObj['id']), headers=headers, body=jsonObj)
            self.assertEqual(result.status_code, 200)
            self.assertEqual(playerObj, result.json) 

            # Test delete
            del headers['Content-Length']
            result = self.simulate_delete('/players/{0}'.format(playerObj['id']), headers=headers)
            self.assertEqual(result.status_code, 204)

if __name__ == '__main__':
    unittest.main()
