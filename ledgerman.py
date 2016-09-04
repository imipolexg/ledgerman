#!/usr/bin/env python3

from models import Player, Game, GameEvent, sql_obj_to_json, init_db
import falcon
import hashlib
import sqlobject
import json

def gen_api_token():
    h = hashlib.new('md5')
    h.update(
        'In real life we would generate random api tokens for clients and store them in a table')
    return h.hexdigest()

api_token = gen_api_token()

class APITokenMiddleware(object):
    """Middleware to verify that a valid API token is present on the request
    """

    def process_request(self, req, resp):
        token = req.get_header('X-API-Token')

        if token is None or not self._check_token(token):
            title = 'Bad API token'
            description = 'Token ' + str(token )+ \
                ' is invalid. Please provide a valid API token in the X-API-Token header'

            raise falcon.HTTPBadRequest(title, description)

    def _check_token(self, token):
        return token == api_token


class Resource(object):

    def __init__(self, typeString, sqlObj):
        self.typeString = typeString
        self.sqlObj = sqlObj

    def _list_all(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = sql_obj_to_json(
            self.typeString, list(self.sqlObj.select()))

    def _get_one(self, req, resp, resourceId):
        try:
            resource = self.sqlObj.get(resourceId)
            resp.status = falcon.HTTP_200
            resp.body = sql_obj_to_json(self.typeString, resource)
        except sqlobject.SQLObjectNotFound:
            raise falcon.HTTPNotFound()


class PlayerResource(Resource):

    def __init__(self):
        super(PlayerResource, self).__init__('player', Player)

    def on_get(self, req, resp, playerId=None, gameId=None):
        if playerId is None and gameId is None:
            self._list_all(req, resp)
        elif gameId is not None:
            self._get_players_for_game(req, resp, gameId)
        else:
            self._get_one(req, resp, playerId)

    def on_patch(self, req, resp, playerId=None):
        if playerId is None:
            raise falcon.HTTPBadRequest('Bad Request', 'No id provided')

        player = None
        try:
            player = Player.get(playerId)
        except SQLObjectNotFound:
            raise falcon.HTTPNotFound()

        patchObj = None
        try:
            patchObj = json.loads(req.stream.read())
            if patchObj['id'] != playerId:
                raise ValueError('ID mismatch') 

            if patchObj['type'] != self.typeString:
                raise ValueError('Type mismatch')

            if not patchObj.has_key('attributes'):
                raise ValueError('Missing attributes key')

        except (ValueError, KeyError) as ex:
            raise falcon.HTTPBadRequest('Invalid Request Object', ex.message) 

        attrs = patchObj['attributes']


    def _get_players_for_game(self, req, resp, gameId):
        try:
            game = Game.get(gameId)
        except SQLObjectNotFound:
            raise falcon.HTTPNotFound()

        resp.status = falcon.HTTP_200
        resp.body = sql_obj_to_json(self.typeString, game.players)

class GameResource(Resource):

    def __init__(self):
        super(GameResource, self).__init__('game', Game)

    def on_get(self, req, resp, playerId=None, gameId=None):
        if playerId is None and gameId is None:
            self._list_all(req, resp)
        elif playerId is not None:
            self._get_games_for_player(req, resp, playerId)
        else:
            self._get_one(req, resp, gameId)

    def _get_games_for_player(self, req, resp, playerId):
        try:
            player = Player.get(playerId)
        except SQLObjectNotFound:
            raise falcon.HTTPNotFound()

        resp.status = falcon.HTTP_200
        resp.body = sql_obj_to_json(self.typeString, player.games)

init_db()

app = falcon.API(middleware=[APITokenMiddleware()])
players = PlayerResource()
games = GameResource()

# Routes

app.add_route('/players', players)
app.add_route('/players/{playerId}', players)
app.add_route('/players/{playerId}/games', games)
#app.add_route('/players/{playerId}/events', events)

app.add_route('/games', games)
app.add_route('/games/{gameId}', games)
app.add_route('/games/{gameId}/players', players)
# app.add_route('/games/{gameId}/events', events)
