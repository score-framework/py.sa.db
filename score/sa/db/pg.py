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

"""
Provides functions specific to PostgreSQL databases.
"""

import logging
import transaction

log = logging.getLogger(__name__)


def list_views(connection):
    """
    Returns a list of view names from the current database's public schema.
    """
    sql = "SELECT table_name FROM information_schema.tables "\
        "WHERE table_schema='public' AND table_type='VIEW'"
    return [name for (name, ) in connection.execute(sql)]


def list_tables(connection):
    """
    Returns a list of table names from the current database's public schema.
    """
    sql = "SELECT table_name FROM information_schema.tables "\
        "WHERE table_schema='public' AND table_type='BASE TABLE'"
    return [name for (name, ) in connection.execute(sql)]


def list_sequences(connection):
    """
    Returns a list of the sequence names from the current
    database's public schema.
    """
    sql = "SELECT sequence_name FROM information_schema.sequences "\
        "WHERE sequence_schema='public'"
    return [name for (name, ) in connection.execute(sql)]


def list_enum_types(connection):
    """
    Returns a list of enum type names from the current database.
    """
    sql = "SELECT typname FROM pg_type WHERE typtype = 'e'"
    return [name for (name, ) in connection.execute(sql)]


def destroy(connection, destroyable):
    """
    Drops everything in the database – tables, views, sequences, etc. For
    safety reasons, the *destroyable* flag of the database
    :class:`configuration <score.sa.db.ConfiguredSaDbModule>` must be passed as
    parameter.
    """
    assert destroyable
    with transaction.manager:
        for seq in list_sequences(connection):
            connection.execute('DROP SEQUENCE "%s" CASCADE' % seq)
        for view in list_views(connection):
            connection.execute('DROP VIEW "%s" CASCADE' % view)
        for enum_type in list_enum_types(connection):
            connection.execute('DROP TYPE "%s" CASCADE' % enum_type)
        for table in list_tables(connection):
            connection.execute('DROP TABLE "%s" CASCADE' % table)
