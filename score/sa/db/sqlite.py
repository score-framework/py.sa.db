# Copyright © 2017,2018 STRG.AT GmbH, Vienna, Austria
# Copyright © 2019-2023 Necdet Can Ateşman, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in
# the file named COPYING.LESSER.txt.
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
# the discretion of STRG.AT GmbH also the competent court, in whose district
# the Licensee has his registered seat, an establishment or assets.


import sqlalchemy as sa


def list_tables(connection):
    """
    Returns a list of all table names.
    """
    sql = sa.text("SELECT name FROM sqlite_master WHERE type = 'table'")
    return [name for (name, ) in connection.execute(sql)]


def list_views(connection):
    """
    Returns a list of all view names.
    """
    sql = sa.text("SELECT name FROM sqlite_master WHERE type = 'view'")
    return [name for (name, ) in connection.execute(sql)]


def list_triggers(connection):
    """
    Returns a list of all trigger names.
    """
    sql = sa.text("SELECT name FROM sqlite_master WHERE type = 'trigger'")
    return [name for (name, ) in connection.execute(sql)]


def destroy(connection, destroyable):
    """
    Drops everything in the database – tables, views, sequences, etc. For
    safety reasons, the *destroyable* flag of the database
    :class:`configuration <score.sa.db.ConfiguredSaDbModule>` must be passed as
    parameter.
    """
    assert destroyable
    transaction = connection.begin()
    try:
        connection.execute(sa.text("PRAGMA foreign_keys=OFF"))
        for trigger in list_triggers(connection):
            connection.execute(sa.text('DROP TRIGGER "%s"' % trigger))
        for view in list_views(connection):
            connection.execute(sa.text('DROP VIEW "%s"' % view))
        for table in list_tables(connection):
            connection.execute(sa.text('DROP TABLE "%s"' % table))
        connection.execute(sa.text("VACUUM"))
        connection.execute(sa.text("PRAGMA foreign_keys=ON"))
        transaction.commit()
    except:
        transaction.rollback()
        raise
