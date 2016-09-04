from datetime import datetime
from sqlobject import *
import json
import os
import re
import sys


class Player(SQLObject):
    name = UnicodeCol()
    handle = UnicodeCol()
    email = UnicodeCol()
    avatarURL = UnicodeCol()
    uuid = UnicodeCol()
    games = RelatedJoin('Game')
    events = MultipleJoin('GameEvent')


class Game(SQLObject):
    startedAt = DateTimeCol()
    endedAt = DateTimeCol()
    gameType = EnumCol(enumValues=('ffa', 'duel', 'ctf'))
    winner = ForeignKey('Player')
    players = RelatedJoin('Player')
    events = MultipleJoin('GameEvent')


class GameEvent(SQLObject):
    game = ForeignKey('Game')
    timestamp = DateTimeCol()
    eventType = EnumCol(enumValues=(
        'joined', 'left', 'spawned', 'damaged', 'fragged'))
    player = ForeignKey('Player')
    to = ForeignKey('Player')


def camel_to_dash(camel):
    """oneTwoThree becomes one-two-three"""
    return re.sub(r'([a-z1-9]+)([A-Z1-9]+)', r'\1-\2', camel).lower()


def dash_to_camel(dash):
    """one-two-three becomes oneTwoThree"""
    words = dash.split('-')
    return ''.join([words[0]] + [x.capitalize() for x in words[1:]])


def sql_obj_to_dict(typeString, sqlObj):
    """Converts an SQLObject to a dict in a roughly JSON API format"""
    attributes = dict((camel_to_dash(col), getattr(sqlObj, col))
                      for col in sqlObj.sqlmeta.columns)
    objDict = {
        'id': sqlObj.id,
        'type': typeString,
        'attributes': attributes
    }

    return objDict


def sql_obj_to_json(typeString, sqlObj):
    """Converts an SQLObject, or list of objects to a JSON object or array of objects"""
    result = None
    if type(sqlObj) is list:
        result = [sql_obj_to_dict(typeString, x) for x in sqlObj]
    else:
        result = sql_obj_to_dict(typeString, sqlObj)

    return json.dumps(result, default=lambda x: str(x))


def init_db(db='agoratest.db'):
    dbPath = os.path.abspath(db)
    # if db file exists we assume it's been migrated
    dbExists = os.path.exists(dbPath)
    conn = connectionForURI('sqlite:' + dbPath)
    sqlhub.processConnection = conn

    if not dbExists:
        for table in (Player, Game, GameEvent):
            table.createTable()

if __name__ == '__main__':
    initDb()
