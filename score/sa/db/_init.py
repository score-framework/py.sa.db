# Copyright © 2017,2018 STRG.AT GmbH, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in the
# file named COPYING.LESSER.txt.
#
# The SCORE Framework and all its parts are distributed without any WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. For more details see the GNU Lesser General Public
# License.
#
# If you have not received a copy of the GNU Lesser General Public License see
# http://www.gnu.org/licenses/.
#
# The License-Agreement realised between you as Licensee and STRG.AT GmbH as
# Licenser including the issue of its valid conclusion and its pre- and
# post-contractual effects is governed by the laws of Austria. Any disputes
# concerning this License-Agreement including the issue of its valid conclusion
# and its pre- and post-contractual effects are exclusively decided by the
# competent court, in whose district STRG.AT GmbH has its registered seat, at
# the discretion of STRG.AT GmbH also the competent court, in whose district the
# Licensee has his registered seat, an establishment or assets.

import sqlalchemy as sa
from score.init import (
    ConfiguredModule, parse_dotted_path, parse_bool, parse_call)


defaults = {
    'destroyable': False,
    'ctx.member': 'db',
    'ctx.transaction': True,
}


def init(confdict, ctx=None):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:

    :confkey:`sqlalchemy.*`
        All configuration values under this key will be passed to
        :func:`engine_from_config`, which in turn calls
        :func:`sqlalchemy.create_engine` with these configuration values as
        keyword arguments. Usually the following is sufficient::

            sqlalchemy.url = postgresql://dbuser@localhost/projname

    :confkey:`destroyable` :confdefault:`False`
        Whether destructive operations may be performed on the database. This
        value prevents accidental deletion of important data on live servers.

        Note that any application feature destroying data must consult this flag
        before proceeding!

    :confkey:`ctx.member` :confdefault:`db`
        The name of the :term:`context member` providing an
        :class:`sqlalchemy.engine.Connection`. Can be the string `None` to
        indicate, that no context member should be registered.

        This value is only relevant, if the optional :mod:`score.ctx` dependency
        was configured.

    :confkey:`ctx.transaction` :confdefault:`True`
        Whether the context member providing the context-scoped database
        connection should wrap the connection in a transaction. The transaction
        will be committed at the end of the context object's lifecycle (or
        rolled back, if the context was terminated with an uncaught exception).

        This value is only relevant if *ctx.member* is not `None`.

    """
    conf = defaults.copy()
    conf.update(confdict)
    engine = engine_from_config(conf)
    ctx_member = None
    if conf['ctx.member'] and conf['ctx.member'] != 'None':
        ctx_member = conf['ctx.member']
    if conf['ctx.transaction']:
        ctx_transaction = parse_bool(conf['ctx.transaction'])
    return ConfiguredSaDbModule(
        ctx, engine, parse_bool(conf['destroyable']),
        ctx_member, ctx_transaction)


_registered_utf8mb4 = False


def engine_from_config(config):
    """
    A wrapper around :func:`sqlalchemy.engine_from_config`, that converts
    certain configuration values. Currently, the following configurations are
    processed:

    - ``sqlalchemy.echo`` (using :func:`score.init.parse_bool`)
    - ``sqlalchemy.echo_pool`` (using :func:`score.init.parse_bool`)
    - ``sqlalchemy.case_sensitive`` (using :func:`score.init.parse_bool`)
    - ``sqlalchemy.module`` (using :func:`score.init.parse_dotted_path`)
    - ``sqlalchemy.poolclass`` (using :func:`score.init.parse_dotted_path`)
    - ``sqlalchemy.pool`` (using :func:`score.init.parse_call`)
    - ``sqlalchemy.pool_size`` (converted to `int`)
    - ``sqlalchemy.pool_recycle`` (converted to `int`)
    """
    global _registered_utf8mb4
    conf = dict()
    for key in config:
        if key in ('sqlalchemy.echo', 'sqlalchemy.echo_pool',
                   'sqlalchemy.case_sensitive'):
            conf[key] = parse_bool(config[key])
        elif key in ('sqlalchemy.module', 'sqlalchemy.poolclass'):
            conf[key] = parse_dotted_path(config[key])
        elif key == 'sqlalchemy.pool':
            conf[key] = parse_call(config[key])
        elif key in ('sqlalchemy.pool_size', 'sqlalchemy.pool_recycle'):
            conf[key] = int(config[key])
        else:
            conf[key] = config[key]
    if not _registered_utf8mb4 and 'utf8mb4' in conf.get('sqlalchemy.url', ''):
        import codecs
        codecs.register(lambda name: codecs.lookup('utf8')
                        if name == 'utf8mb4' else None)
        _registered_utf8mb4 = True
    return sa.engine_from_config(conf)


class ConfiguredSaDbModule(ConfiguredModule):
    """
    This module's :class:`configuration class
    <score.init.ConfiguredModule>`.
    """

    def __init__(self, ctx, engine, destroyable, ctx_member, ctx_transaction):
        super().__init__(__package__)
        self.ctx = ctx
        self.engine = engine
        self.destroyable = destroyable
        self.ctx_member = ctx_member
        self.ctx_transaction = ctx_transaction
        self.__ctx_connections = dict()
        if ctx and ctx_member:
            ctx.register(ctx_member,
                         self._create_connection,
                         self._close_connection)

    def get_connection(self, ctx):
        """
        Provides an :class:`sqlalchemy.engine.Connection` for given
        :class:`score.ctx.Context` object. The connection will have an active
        transaction that will be committed (or rolled back in case of an error)
        at the end of the context lifetime.
        """
        assert isinstance(ctx, self.ctx.Context)
        return getattr(ctx, self.ctx_member)

    def _create_connection(self, ctx):
        if ctx not in self.__ctx_connections:
            connection = self.engine.connect()
            transaction = None
            if self.ctx_transaction:
                transaction = connection.begin()
            self.__ctx_connections[ctx] = {
                'connection': connection,
                'transaction': transaction,
            }
        return self.__ctx_connections[ctx]['connection']

    def _close_connection(self, ctx, connection, exception):
        try:
            transaction = self.__ctx_connections[ctx]['transaction']
            if transaction:
                if exception:
                    transaction.rollback()
                else:
                    transaction.commit()
        finally:
            connection.close()
            del self.__ctx_connections[ctx]

    def destroy(self, connection=None):
        """
        .. note::
            This function currently only works on postgresql and sqlite
            databases.

        Drops everything in the database – tables, views, sequences, etc.
        This function will not execute if the database configuration was not
        explicitly set to be *destroyable*.
        """
        assert self.destroyable
        if self.engine.dialect.name == 'postgresql':
            from .pg import destroy
        elif self.engine.dialect.name == 'sqlite':
            from .sqlite import destroy
        else:
            raise Exception('Can only destroy sqlite and postgresql databases')
        if connection is None:
            connection = self.engine.connect()
        destroy(connection, self.destroyable)
