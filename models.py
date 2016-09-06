from datetime import datetime
from sqlobject import *
import formencode
import json
import os
import re
import sys


class LedgermanModel(SQLObject):
    """Base class for our resource objects. Can construct or update itself from json"""

    # Format for datetime strings
    isofmt = '%Y-%m-%d %H:%M:%S'
    isofmt_ms = '%Y-%m-%d %H:%M:%S.%f'

    @classmethod
    def parse_json_payload(cls, jsonPayload, typeString, resourceId=None, update=False):
        """Converts a JSON payload into a dict with some basic validation."""
        jsonObj = json.loads(jsonPayload)

        # First, some validation

        # We want JSON object, not a list or a str, integer, etc.
        if type(jsonObj) != dict:
            raise ValueError('Not a JSON object')

        # Check that the URL for the PATCH matches the id in the payload
        if resourceId and jsonObj['id'] != int(resourceId) and update:
            raise ValueError('ID mismatch')

        if not jsonObj.has_key('type'):
            raise ValueError("Missing 'type' property")

        if jsonObj['type'] != typeString:
            raise ValueError('Type mismatch')

        if not jsonObj.has_key('attributes'):
            raise ValueError("Missing 'attributes' property")

        # Parse the attributes
        attrs = {}
        for k, v in jsonObj['attributes'].iteritems():
            attrName = dash_to_camel(k)
            # Don't complain if the attribute in the json doesn't exist on the object 
            if cls.sqlmeta.columns.has_key(attrName):
                colDef = cls.sqlmeta.columns[attrName]
                attrs[attrName] = cls.parse_value(attrName, colDef, v)

        return attrs

    @classmethod
    def parse_value(cls, attrName, columnDef, value):
        if value is None:
            return value

        columnType = type(columnDef)
        if columnType == SODateTimeCol:
            value = cls.parse_datetime(attrName, value)
        elif columnType == SOForeignKey:
            value = cls.parse_id_value(attrName, columnDef, value)

        return value

    @classmethod
    def parse_id_value(cls, attrName, columnDef, value):
        """Ensures that the id passed to a relational property points to an existing object.

        Will also throw ValueError if id is not an integer"""

        foreignClass = columnDef.foreignKey
        try:
            globals()[foreignClass].get(value)
        except SQLObjectNotFound:
            raise ValueError("'{0}' must be set to null or to the id of an existing {1}".format(
                attrName, foreignClass))
        except ValueError:
            raise ValueError("'{0}' must be set to null or an integer".format(attrName))

        return value

    @classmethod
    def parse_datetime(cls, attrName, dtval):
        try:
            if dtval.rfind('.') == -1:
                dt = datetime.strptime(dtval, cls.isofmt)
            else:
                dt = datetime.strptime(dtval, cls.isofmt_ms)
        except (ValueError, AttributeError):
            raise ValueError(
                "'{0}' should be a strptime() date string formatted thus: '{1}'".format(attrName, cls.isofmt_ms))

        return dt

    @classmethod
    def create_from_json(cls, jsonPayload, typeString):
        attrs = cls.parse_json_payload(jsonPayload, typeString)
        try:
            return cls(**attrs)
        except formencode.api.Invalid as ex:
            raise ValueError(str(ex))

    def update_from_json(self, jsonPayload, typeString):
        attrs = self.parse_json_payload(jsonPayload, typeString, self.id, True)

        for k, v in attrs.iteritems():
            try:
                setattr(self, k, v)
            except formencode.api.Invalid as ex:
                raise ValueError(str(ex))

    def to_json_dict(self, typeString):
        """Converts an SQLObject to a dict suitable for dumping to JSON

        We don't call json.dumps here to emit a text representation because we
        want to use this to construct lists of objects and the only call
        json.dumps() once on that list."""

        attributes = dict((camel_to_dash(col), getattr(self, col)) for col in self.sqlmeta.columns)
        jsonDict = {
            'id': self.id,
            'type': typeString,
            'attributes': attributes
        }

        return jsonDict


class Player(LedgermanModel):
    achievements = MultipleJoin('Achievement')
    avatarUrl = UnicodeCol()
    email = UnicodeCol()
    events = MultipleJoin('GameEvent')
    games = RelatedJoin('Game')
    handle = UnicodeCol()
    name = UnicodeCol()


class Game(LedgermanModel):
    achievements = RelatedJoin('Achievement')
    endedAt = DateTimeCol()
    events = MultipleJoin('GameEvent')
    gameType = EnumCol(enumValues=('ffa', 'duel', 'ctf'))
    players = RelatedJoin('Player')
    startedAt = DateTimeCol()
    winner = ForeignKey('Player')
    active = BoolCol()


class GameEvent(LedgermanModel):
    game = ForeignKey('Game')
    eventType = EnumCol(enumValues=('joined', 'left', 'spawned', 'damaged', 'fragged'))
    player = ForeignKey('Player')
    timestamp = DateTimeCol()
    to = ForeignKey('Player')


class AchievementType(LedgermanModel):
    name = UnicodeCol()


class Achievement(LedgermanModel):
    achievementType = ForeignKey('AchievementType')
    # The game in which the achievement was ... achieved
    game = ForeignKey('Game')
    player = ForeignKey('Player')
    timestamp = DateTimeCol()


camel_to_dash_re = re.compile(r'([a-z1-9]+)([A-Z1-9]+)')


def camel_to_dash(camel):
    """Converts 'oneTwoThree' into 'one-two-three'"""
    return camel_to_dash_re.sub(r'\1-\2', camel).lower()


def dash_to_camel(dash):
    """Converts 'one-two-three' into 'oneTwoThree'

    SQLObject converts ForeignKey attributes into propertyID columns instead of
    propertyId, so this method will convert property-id into propertyID as
    well.
    """
    words = dash.split('-')
    if words[-1].lower() == 'id':
        camel = ''.join([words[0]] + [x.capitalize() for x in words[1:-1]] + [words[-1].upper()])
    else:
        camel = ''.join([words[0]] + [x.capitalize() for x in words[1:]])

    return camel


def dump_json(obj, typeString):
    """Converts an SQLObject, or list of objects to a JSON object or array of objects"""
    result = None
    if type(obj) is list:
        result = [x.to_json_dict(typeString) for x in obj]
    else:
        result = obj.to_json_dict(typeString)

    return json.dumps(result, default=lambda x: str(x))


def init_db(db='ledgerman.db'):
    """Set up the SQLObject database connection"""

    conn = None
    dbExists = False

    if db == ':memory:':
        conn = connectionForURI('sqlite:/:memory:')
    else:
        dbPath = os.path.abspath(db)
        # if db file exists we assume it's been migrated
        dbExists = os.path.exists(dbPath)
        conn = connectionForURI('sqlite:' + dbPath)

    sqlhub.processConnection = conn

    if not dbExists:
        for table in (Player, Game, GameEvent, AchievementType, Achievement):
            table.createTable()
