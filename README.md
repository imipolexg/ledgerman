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

#### Read

#### Update

#### Delete

### Games endpoint

#### Create

#### Read

#### Update

#### Delete

### Game Events endpoint

#### Create

#### Read

#### Update

#### Delete

### Achievements endpoint

#### Create

#### Read

#### Update

#### Delete

### Achievement types endpoint

#### Create

#### Read

#### Update

#### Delete

