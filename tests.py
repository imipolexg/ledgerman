#!/usr/bin/env python
# Some basic CRUD functionality tests for our endpoints. No testing of edge cases yet.
import __builtin__
__builtin__.ledgerman_testing = True
import datetime 
import faker
import falcon
import falcon.testing as testing
import json
import ledgerman
import random
import unittest
from models import dash_to_camel, camel_to_dash

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

    def fake_player(self):
        return {
            'type': 'player',
            'attributes': {
                'email': fake.email(),
                'name': fake.name(),
                'handle': fake.word(),
                'avatar-url': fake.uri()
            }
        }

    def fake_game(self):
        types = ('ffa', 'duel', 'ctf')
        return {
            'type': 'game',
            'attributes': {
                'started-at': str(datetime.datetime.now()),
                'ended-at': None,
                'active': True,
                'game-type': random.choice(types) ,
                'winner-id': None
            }
        }

class UtilTest(LedgermanTest):
    def test_camel_dash(self):
        self.assertEqual(dash_to_camel('one-two-three-four'), 'oneTwoThreeFour')
        self.assertEqual(camel_to_dash('oneTwoThreeFour'), 'one-two-three-four')
        self.assertEqual(camel_to_dash(dash_to_camel('one-two-three-four')), 'one-two-three-four')

    def test_dash_to_camel_id_param(self):
        self.assertEqual(dash_to_camel('a-parameter-id'), 'aParameterID')
        self.assertEqual(camel_to_dash(dash_to_camel('a-parameter-id')), 'a-parameter-id')
       
        # id suffix edge case
        self.assertEqual(dash_to_camel('param-mid'), 'paramMid')


class PlayerTest(LedgermanTest):

    test_object_count = 50

    def test_create(self):
        self.test_objects = []

        for i in range(self.test_object_count):
            playerObj = self.fake_player()
            self.test_objects.append(playerObj.copy())

            jsonObj = json.dumps(playerObj)

            headers = self.headers.copy()

            # test create
            res = self.simulate_post('/players', headers=headers, body=jsonObj)
            self.assertEqual(res.status_code, 200)

            newResObj = res.json
            playerObj['id'] = newResObj['id']

            self.assertEqual(newResObj, playerObj)

    def test_get_all(self): 
        all_players = self.simulate_get('/players', headers=self.headers)
        self.assertEqual(all_players.status_code, 200)
        self.assertEqual(len(all_players.json), self.test_object_count)

    def test_get_one(self):
        all_players = self.simulate_get('/players', headers=self.headers).json
        for i in range(len(all_players)):
            playerId = all_players[i]['id']
            res = self.simulate_get('/players/{0}'.format(playerId), headers=self.headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(all_players[i], res.json)

    def test_update(self):
        all_players = self.simulate_get('/players', headers=self.headers).json
        for i in range(len(all_players)):
            playerId = all_players[i]['id']
            all_players[i]['attributes']['email'] = fake.email()
            patch_json = json.dumps(all_players[i])
            patch_headers = self.headers.copy()

            res = self.simulate_patch('/players/{0}'.format(playerId), headers=patch_headers, body=patch_json)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(all_players[i], res.json)

            res = self.simulate_get('/players/{0}'.format(playerId), headers=self.headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(all_players[i], res.json)

    def test_99_delete(self):
        # Test delete
        for i in range(self.test_object_count):
            res = self.simulate_delete('/players/{0}'.format(i), headers=self.headers)
            self.assertEqual(res.status_code, 204)

class GameTest(LedgermanTest):

    def test_create(self):
        fakeGame = self.fake_game()
        res = self.simulate_post('/games', headers=self.headers, body=json.dumps(fakeGame))
        self.assertEqual(res.status_code, 200)
        createdGame = res.json
        fakeGame['id'] = createdGame['id']
        self.assertEqual(createdGame, fakeGame)


class GameEventTest(LedgermanTest):

    def test_create(self):
        res = self.simulate_post('/players', headers=self.headers, body=json.dumps(self.fake_player()))
        p1 = res.json 
        self.assertEqual(res.status_code, 200)

        res = self.simulate_post('/players', headers=self.headers, body=json.dumps(self.fake_player()))
        p2 = res.json 
        self.assertEqual(res.status_code, 200)
        
        res = self.simulate_post('/games', headers=self.headers, body=json.dumps(self.fake_game()))
        self.assertEqual(res.status_code, 200)
        game = res.json

        joinEvent1 = {
            'type': 'event',
            'attributes': {
                'player-id': p1['id'],
                'timestamp': str(datetime.datetime.now()),
                'to-id': None,
                'event-type': 'joined',
                'game-id': game['id']
            }
        }

        joinEvent2 = {
            'type': 'event',
            'attributes': {
                'player-id': p2['id'],
                'timestamp': str(datetime.datetime.now()),
                'to-id': None,
                'event-type': 'joined',
                'game-id': game['id']
            }
        }

        for evt in (joinEvent1, joinEvent2):
            res = self.simulate_post('/events', headers=self.headers, body=json.dumps(evt))
            self.assertEqual(res.status_code, 200)

        # Check to see if the players are now related to the game
        gamePlayers = self.simulate_get('/games/{0}/players'.format(game['id']), headers=self.headers).json
        self.assertEqual(len(gamePlayers), 2)

        found = 0
        for gplayer in gamePlayers:
            for p in (p1, p2):
                if gplayer['id'] ==  p['id']:
                    found += 1
                    self.assertEqual(p, gplayer)

            # test games-for-player relation
            res = self.simulate_get('/players/{0}/games'.format(p['id']), headers=self.headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(game, res.json[0])

        self.assertEqual(found, 2)

    def test_get_events_for_game(self):
        games = self.simulate_get('/games', headers=self.headers).json
        self.assertTrue(len(games) > 0)
        for g in games:
            res = self.simulate_get('/games/{0}/events'.format(g['id']), headers=self.headers)
            self.assertEqual(res.status_code, 200)

    def test_get_events_for_player(self):
        players = self.simulate_get('/players', headers=self.headers).json
        self.assertTrue(len(players) > 0)
        for p in players:
            res = self.simulate_get('/players/{0}/events'.format(p['id']), headers=self.headers)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(len(res.json) > 0)

    def test_try_event_for_inactive_game(self):
        players = self.simulate_get('/players', headers=self.headers).json
        self.assertTrue(len(players) > 0)

        fakeGame = self.fake_game()
        fakeGame['attributes']['active'] = False
        fakeGame['attributes']['ended-at'] = str(datetime.datetime.now())

        res = self.simulate_post('/games', headers=self.headers, body=json.dumps(fakeGame))
        self.assertEquals(res.status_code, 200)
        game = res.json

        event = {
            'type': 'event',
            'attributes': {
                'player-id': players[0]['id'],
                'timestamp': str(datetime.datetime.now()),
                'to-id': players[1]['id'],
                'event-type': 'fragged',
                'game-id': game['id']
            }
        }
        
        res = self.simulate_post('/events', headers=self.headers, body=json.dumps(event))
        self.assertEquals(res.status_code, 400)
        errorObj = res.json
        self.assertEquals(errorObj['description'], 'Events cannot be created for an inactive game')



if __name__ == '__main__':
    unittest.main()
