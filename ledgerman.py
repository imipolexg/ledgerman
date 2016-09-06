from restfuls import *
from models import init_db
import falcon
import hashlib
import json
import re
import sqlobject
import md5
import __builtin__

class APITokenMiddleware(object):
    """Middleware to verify that a valid API token is present on the request."""

    def __init__(self):
        self.apiToken = self.gen_api_token()

    @staticmethod
    def gen_api_token():
        return md5.md5('In real life we would generate random api tokens for clients and store them in a table').hexdigest()

    def process_request(self, req, resp):
        token = req.get_header('X-API-Token')

        if token is None or not self.check_token(token):
            title = 'Bad API token'
            description = 'X-API-Token header invalid or not present.'

            raise falcon.HTTPBadRequest(title, description)

    def check_token(self, token):
        return token == self.apiToken


class ValidateIdsMiddleware(object):
    """Ensures that any id parameter is a valid integer"""

    def process_resource(self, req, resp, resource, params):
        for k in params:
            if k[-2:] != 'Id': 
                continue

            try:
                params[k] = int(params[k])
            except ValueError:
                raise falcon.HTTPBadRequest('Bad Request', "Parameter '{0}' must be an integer.".format(k))


if hasattr(__builtin__, 'ledgerman_testing') and __builtin__.ledgerman_testing:
    init_db(':memory:')
else:
    init_db()

api = falcon.API(middleware=[APITokenMiddleware(), ValidateIdsMiddleware()])

events = GameEventResource()
eventsCollection = GameEventCollection()
eventsForGame = EventsForGameResource()
eventsForPlayer = EventsForPlayerResource()
games = GameResource()
gamesCollection = GameCollection()
gamesForPlayer = GamesForPlayerResource()
players = PlayerResource()
playersCollection = PlayerCollection()
playersForGame = PlayersForGameResource()
achievements = AchievementResource()
achievementsCollection = AchievementCollection()
achievementTypes = AchievementTypeResource()
achievementTypesCollection = AchievementTypeCollection()
achievementsForPlayer = AchievementsForPlayerResource()
achievementsForGame = AchievementsForGameResource()

# Routes
api.add_route('/players', playersCollection)
api.add_route('/players/{playerId}', players)
api.add_route('/players/{playerId}/games', gamesForPlayer)
api.add_route('/players/{playerId}/events', eventsForPlayer)
api.add_route('/players/{playerId}/achievements', achievementsForPlayer)

api.add_route('/games', gamesCollection)
api.add_route('/games/{gameId}', games)
api.add_route('/games/{gameId}/players', playersForGame)
api.add_route('/games/{gameId}/events', eventsForGame)
api.add_route('/games/{gameId}/achievements', achievementsForGame)

api.add_route('/events', eventsCollection)
api.add_route('/events/{eventId}', events)

api.add_route('/achievement-types', achievementTypesCollection)
api.add_route('/achievement-types/{typeId}', achievementTypes)

api.add_route('/achievements', achievementsCollection)
api.add_route('/achievements/{achievementId}', achievements)
