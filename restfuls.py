from sqlobject import SQLObjectNotFound
from models import Achievement, AchievementType, Player, Game, GameEvent, dump_json, dash_to_camel
import json
import falcon
import formencode

class Resource(object):
    """Base clase for handling resource objects. 
    Handles basic CRUD operations.
    """

    def __init__(self, typeString, sqlObj):
        self.typeString = typeString
        self.sqlObj = sqlObj

    def list_all(self, req, resp):
        resp.body = dump_json(list(self.sqlObj.select()), self.typeString)

    def get_one(self, req, resp, resourceId):
        try:
            resource = self.sqlObj.get(resourceId)
            resp.body = dump_json(resource, self.typeString)
        except SQLObjectNotFound:
            raise falcon.HTTPNotFound()

    def create_one(self, req, resp):
        resource = None
        try:
            resource = self.sqlObj.create_from_json(req.stream.read(), self.typeString)
        except ValueError as ex:
            raise falcon.HTTPBadRequest('Bad Request', ex.message)

        return resource

    def update_one(self, req, resp, resourceId):
        if resourceId is None:
            raise falcon.HTTPBadRequest('Bad Request', 'No id provided')

        resource = None
        try:
            resource = self.sqlObj.get(resourceId)
        except SQLObjectNotFound:
            raise falcon.HTTPNotFound()

        try:
            resource.update_from_json(req.stream.read(), self.typeString)
        except ValueError as ex:
            raise falcon.HTTPBadRequest('Bad Request', ex.message)

        return resource

    def delete_one(self, req, resp, resourceId):
        resp.status = falcon.HTTP_204
        if resourceId is None:
            return

        try:
            self.sqlObj.delete(resourceId)
        except SQLObjectNotFound:
            pass


class OneToManyResource(object):
    """Handles the fetching of one-to-many relationships. 

    E.g., all players for a game, or all games for a player."""

    def __init__(self, theManyTypeString, theOneSqlObj):
        self.typeString = theManyTypeString
        self.sqlObj = theOneSqlObj

    def get_many_for_one(self, req, resp, resourceId, relAttr):
        resource = None
        try:
            resource = self.sqlObj.get(resourceId)
        except SQLObjectNotFound:
            raise falcon.HTTPNotFound()

        resp.status = falcon.HTTP_200
        resp.body = dump_json(getattr(resource, relAttr), self.typeString)


class PlayerResource(Resource):

    def __init__(self):
        super(PlayerResource, self).__init__('player', Player)

    def on_get(self, req, resp, playerId):
        self.get_one(req, resp, playerId)

    def on_patch(self, req, resp, playerId):
        player = self.update_one(req, resp, playerId)
        resp.body = dump_json(player, self.typeString)

    def on_delete(self, req, resp, playerId):
        self.delete_one(req, resp, playerId)


class PlayerCollection(Resource):

    def __init__(self):
        super(PlayerCollection, self).__init__('player', Player)

    def on_get(self, req, resp):
        self.list_all(req, resp)

    def on_post(self, req, resp):
        newPlayer = self.create_one(req, resp)
        resp.body = dump_json(newPlayer, self.typeString)


class PlayersForGameResource(OneToManyResource):

    def __init__(self):
        super(PlayersForGameResource, self).__init__('player', Game)

    def on_get(self, req, resp, gameId):
        self.get_many_for_one(req, resp, gameId, 'players')


class GameResource(Resource):

    def __init__(self):
        super(GameResource, self).__init__('game', Game)

    def on_get(self, req, resp, gameId):
        self.get_one(req, resp, gameId)

    def on_patch(self, req, resp, gameId):
        resource = self.update_one(req, resp, gameId)
        resp.body = dump_json(resource, self.typeString)

    def on_delete(self, req, resp, gameId):
        self.delete_one(req, resp, gameId)


class GameCollection(Resource):

    def __init__(self):
        super(GameCollection, self).__init__('game', Game)

    def on_get(self, req, resp):
        self.list_all(req, resp)

    def on_post(self, req, resp):
        newGame = self.create_one(req, resp)
        resp.body = dump_json(newGame, self.typeString)


class GamesForPlayerResource(OneToManyResource):

    def __init__(self):
        super(GamesForPlayerResource, self).__init__('game', Player)

    def on_get(self, req, resp, playerId):
        player = None
        try:
            player = Player.get(playerId)
        except SQLObjectNotFound:
            raise falcon.HTTPNotFound()

        resp.body = dump_json(player.games, self.typeString)


class GameEventResource(Resource):

    def __init__(self):
        super(GameEventResource, self).__init__('event', GameEvent)

    def on_get(self, req, resp, eventId):
        self.get_one(req, resp, eventId)

    # No PATCH or DELETE for events. 


class GameEventCollection(Resource):

    def __init__(self):
        super(GameEventCollection, self).__init__('event', GameEvent)

    def on_get(self, req, resp):
        self.list_all(req, resp)

    def on_post(self, req, resp):
        newEvent = None
        try:
            attrs = GameEvent.parse_json_payload(req.stream.read(), self.typeString)

            try:
                game = Game.get(attrs['gameID'])
            except KeyError:
                raise ValueError("Missing 'game-id' attribute")

            if not game.active:
                raise ValueError('Events cannot be created for an inactive game')

            newEvent = GameEvent(**attrs)
        except ValueError as ex:
            raise falcon.HTTPBadRequest('Bad Request', ex.message)
        except formencode.api.Invalid as ex:
            raise falcon.HTTPBadRequest('Bad Request', str(ex))

        # Mark when a player joins a game. Everyone who ever joined the game is
        # part of the game's players, even if they leave.
        if newEvent.eventType == 'joined':
            game = newEvent.game
            player = newEvent.player

            if player not in game.players:
                game.addPlayer(player)


class EventsForPlayerResource(OneToManyResource):

    def __init__(self):
        super(EventsForPlayerResource, self).__init__('event', Player)

    def on_get(self, req, resp, playerId):
        self.get_many_for_one(req, resp, playerId, 'events')


class EventsForGameResource(OneToManyResource):

    def __init__(self):
        super(EventsForGameResource, self).__init__('event', Game)

    def on_get(self, req, resp, gameId):
        self.get_many_for_one(req, resp, gameId, 'events')


class AchievementTypeResource(Resource):

    def __init__(self):
        super(AchievementTypeResource, self).__init__('achievement-type', AchievementType)

    def on_get(self, req, resp, achievementTypeId):
        self.get_one(req, resp, playerId)

    def on_patch(self, req, resp, achievementTypeId):
        achievementType = self.update_one(req, resp, playerId)

        resp.body = dump_json(achievementType, self.typeString)

    def on_delete(self, req, resp, achievementTypeId):
        self.delete_one(req, resp, achievementTypeId)


class AchievementTypeCollection(Resource):

    def __init__(self):
        super(AchievementTypeCollection, self).__init__('achievement-type', AchievementType)

    def on_get(self, req, resp):
        self.list_all(req, resp)

    def on_post(self, req, resp):
        newAchievementType = self.create_one(req, resp)
        resp.body = dump_json(newAchievementType, self.typeString)


class AchievementResource(Resource):

    def __init__(self):
        super(AchievementResource, self).__init__('achievement', Achievement)

    def on_get(self, req, resp, achievementId):
        self.get_one(req, resp, playerId)

    def on_patch(self, req, resp, achievementId):
        achievement = self.update_one(req, resp, playerId)

        resp.body = dump_json(achievement, self.typeString)

    def on_delete(self, req, resp, achievementId):
        self.delete_one(req, resp, achievementId)


class AchievementCollection(Resource):

    def __init__(self):
        super(AchievementCollection, self).__init__('achievement-type', Achievement)

    def on_get(self, req, resp):
        self.list_all(req, resp)

    def on_post(self, req, resp):
        newAchievement = self.create_one(req, resp)
        resp.body = dump_json(newAchievement, self.typeString)
