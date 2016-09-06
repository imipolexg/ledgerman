# Ledgerman

Ledgerman is a simple RESTful webservice for storing player and game data.

## Prerequisites

Ledgerman depends on a few packages easily available via `pip`

* [`falcon`](https://github.com/falconry/falcon) - The Falcon web microframework
* [`sqlobject`](http://sqlobject.org/) - An ORM for SQL databases

You'll also need a WSGI webserver. I've been using [Gunicorn](http://gunicorn.org/).

So just run:

	pip install falcon sqlobject gunicorn

And you're good to go.

## Running

If you're using `gunicorn` then getting the app running on localhost is as easy as:

	gunicorn ledgerman:api

## API

Ledgerman provides a straightforward, stateless API on a RESTful model where
HTTP verbs (`POST`, `GET`, `PATCH`, and `DELETE`) have the expected CRUD
effects.

`POST`, `GET` and `PATCH` endpoints all emit either JSON objects or JSON
arrays. `POST` and `PATCH` endpoints accept a JSON object structed identically
to the ones returned by `GET` on a specific object, (with the exception that an
`id` property on `POST` objects will be ignored, since the database will
generate the object's id).

### API token

The HTTP header `X-API-Token` must accompany each request to the ledgerman API
and must be set to a valid API token. In a real version of this app we'd
authenticate users somehow and then allow them to generate and invalidate API
tokens to suit their needs. But for now, there is a single API token:

	71645d46f5d7a03a974dcca8db8e0066    

Which is simply the hexadecimal representatino of the md5 hash of 

	In real life we would generate random api tokens for clients and store them in a table

So set the header like this:

	X-API-Token: 71645d46f5d7a03a974dcca8db8e0066	

### Players endpoint

#### Create

    POST /players

    {
        "type": "player",
        "attributes": {
            "email": "hamm.zachary@gmail.com",
            "name": "Zachary Hamm",
            "handle": "zack",
            "avatar-url": null
        }
    }


If an email is present, but `avatar-url` is null, the API will generate a
[Gravatar](https://www.gravatar.com) for the player. So the above should
generate the following response:

    {
        "attributes": {
            "avatar-url": "https://www.gravatar.com/avatar/247862cb7362f8ea2518efd00c6c2c5b",
            "handle": "zack",
            "email": "hamm.zachary@gmail.com",
            "name": "Zachary Hamm"
        },
        "type": "player",
        "id": 1
    }

#### Read


#### Get a single object

    GET /players/1

    {
        "attributes": {
            "avatar-url": "https://www.gravatar.com/avatar/247862cb7362f8ea2518efd00c6c2c5b",
            "handle": "zack",
            "email": "hamm.zachary@gmail.com",
            "name": "Zachary Hamm"
        },
        "type": "player",
        "id": 1
    }

#### Get all objects

    GET /players

    [
        {
            "attributes": {
                "avatar-url": "https://www.gravatar.com/avatar/247862cb7362f8ea2518efd00c6c2c5b",
                "handle": "zack",
                "email": "hamm.zachary@gmail.com",
                "name": "Zachary Hamm"
            },
            "type": "player",
            "id": 1
        },
        {
            ...
        },
        ...
    ]

#### Update

    PATCH /players/1

    {
        "type": "player",
        "id": 1,
        "attributes": {
            "email": "hamm.zachary@gmail.com",
            "name": "Zachary S. Hamm",
            "handle": "zack",
            "avatar-url": "https://www.gravatar.com/avatar/247862cb7362f8ea2518efd00c6c2c5b"
        }
    }

An identical object should be returned, unless avatar-url is set to null and
email is set, in which case a gravatar will be generated the same as on a POST.

#### Delete

    DELETE /players/1

Will return a `204 No Content` whether or not the object existed.

### Games endpoint

This endpoint will function more or less the same as the `/players` endpoint.
The "active" attribute controls whether or not the `/events` endpoint will
continue to accept event objects related to respective game. The "game-type"
attribute must be set to either "ffa", "ctf", "duel" or null.
    
#### CRUD 

##### A new game

    POST /games

    {
        "type": "game",
        "attributes": {
            "started-at": "2016-09-05 12:00:00"
            "ended-at": null,
            "active": true,
            "winner-id": null,
            "game-type": "ffa"
        }
    }

Result:

    {
        "type": "game",
        "id": 1,
        "attributes": {
            "started-at": "2016-09-05 12:00:00"
            "ended-at": null,
            "active": true,
            "winner-id": null,
            "game-type": "ffa"
        }
    }

##### PATCH to indicate a game is done

    PATCH /games/1

    {
        "type": "game",
        "id": 1,
        "attributes": {
            "started-at": "2016-09-05 12:00:00"
            "ended-at": "2016-09-05 12:30:00",
            "active": false,
            "winner-id": 1 ,
            "game-type": "ffa"
        }
    }

### Game Events endpoint

Game Events must be related to a "active" game object. They also have an "event-type" property which must be one of

    * joined
    * left
    * spawned
    * fragged
    * damaged

They also take a "player-id" and "to-id", the latter being the target of any
transitive actions (Player 1 frags Player 2).

A 'joined' event adds the player to the `/games/{id}/players` relationship and
the game to the `/players/{id}/games` relationships. 

#### Create

    POST /events

    {
        "type": "event",
        "attributes": {
            "game-id": 1
            "event-type": "spawned",
            "player-id": 1
            "timestamp": "12-09-06 01:00:00",
            "to": null
        }
    }

### Achievements

TODO
