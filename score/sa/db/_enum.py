# Copyright © 2015,2016 STRG.AT GmbH, Vienna, Austria
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

# The contents of this file were inspired by a blog post by Mike Bayer but
# written from scratch with the use of python's own enum package, which was
# introduced in Python 3.4. The original blog post can be found here:
# http://techspot.zzzeek.org/2011/01/14/the-enum-recipe/

import enum
from sqlalchemy.types import SchemaType, TypeDecorator, Enum as SAEnum
import re


class Enum(enum.Enum):
    """
    Enumeration class that can be used in database classes.
    """

    def __init__(self, *args):
        cls = self.__class__
        if any(self.value == e.value for e in cls):
            a = self.name
            e = cls(self.value).name
            raise ValueError(
                "Duplicate value in score.db.Enum:  %r --> %r"
                % (a, e))

    @classmethod
    def db_type(cls):
        """
        Returns the SQLAlchemy type to use for storing values of this enum in
        the database.
        """
        return EnumType(cls)


class EnumType(SchemaType, TypeDecorator):

    def __init__(self, enum):
        self.enum = enum
        self.impl = SAEnum(
            *[sym.value for sym in enum],
            name="enum%s" % re.sub(
                '([A-Z])',
                lambda m: "_" + m.group(1).lower(),
                enum.__name__)
        )

    def _set_table(self, table, column):
        self.impl._set_table(table, column)

    def copy(self):
        return EnumType(self.enum)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum(value.strip())
