.. module:: score.sa.db
.. role:: faint
.. role:: confkey

***********
score.sa.db
***********

This module provides functions and classes for accessing databases
conveniently using SQLAlchemy_.

Quickstart
==========

Add the `SQLAlchemy url`_ to your SCORE configuration:

.. code-block:: ini

    [score.init]
    modules =
        db

    [db]
    sqlalchemy.url = sqlite:///${here}/database.sqlite3

Access the configured :class:`sqlalchemy.engine.Engine` as
:attr:`score.db.engine <ConfiguredSaDbModule.engine>`.

>>> connection = score.db.engine.connection()
>>> connection.execute('SELECT 1')

If you have also onfigured :mod:`score.ctx`, you can retrieve a connection with
a transaction that has the same scope as the :class:`Context
<score.ctx.Context>` object itself: The transaction will be automatically
committed at the end of the transaction on success (or rolled back, if the
context is destroyed by an uncaught exception):

>>> with score.ctx.Context() as ctx:
>>>     ctx.db.execute('SELECT 1')


Configuration
=============

.. autofunction:: score.sa.db.init


Details
=======

.. _sa_db_enumerations:

Enumerations
------------

This module provides an Enum class that can be used to interface enumerations
in the database. It sub-classes python's built-in :class:`enum.Enum` type and
adds a function to extract an appropriate SQLAlchemy type:

.. code-block:: python

    from score.sa.db import Enum
    import sqlalchemy as sa

    class Status(Enum):
        ONLINE = 'online'
        OFFLINE = 'offline'

    table = sa.Table('content', metadata,
        Column('status', Status.db_type(), nullable=False),
        ...


API
===

Configuration
-------------

.. autofunction:: init

.. autoclass:: ConfiguredSaDbModule

    .. attribute:: engine

        An SQLAlchemy :class:`Engine <sqlalchemy.engine.Engine>`.

    .. attribute:: destroyable

        Whether destructive operations may be performed on the database. This
        value will be consulted before any such operations are performed.
        Application developers are also advised to make use of this value
        appropriately.

    .. automethod:: destroy

Helper Functions
----------------

.. autofunction:: engine_from_config

Postgresql-Specific
```````````````````

.. autofunction:: score.sa.db.pg.destroy

.. autofunction:: score.sa.db.pg.list_sequences

.. autofunction:: score.sa.db.pg.list_tables

.. autofunction:: score.sa.db.pg.list_views

SQLite-Specific
```````````````

.. autofunction:: score.sa.db.sqlite.destroy

.. autofunction:: score.sa.db.sqlite.list_tables

.. autofunction:: score.sa.db.sqlite.list_triggers

.. autofunction:: score.sa.db.sqlite.list_views

.. _SQLAlchemy: http://docs.sqlalchemy.org/en/latest/
.. _SQLAlchemy url: http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls
