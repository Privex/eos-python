from abc import abstractmethod
from os.path import expanduser, join
from typing import List, Tuple

from privex.db import SqliteWrapper, GenericDBWrapper

SQLITE_SCHEMA = [
    (
        'nodes',
        
        "CREATE TABLE nodes ("
        "   id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, network TEXT NOT NULL,"
        "   enabled INTEGER DEFAULT 1, last_success TIMESTAMP NULL, fail_count INTEGER DEFAULT 0,"
        "   last_fail TIMESTAMP NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "   UNIQUE(url, network) ON CONFLICT ABORT"
        ");",
    ),
    
    (
        'node_api',
        
        "CREATE TABLE node_api ("
        "   node_id INTEGER NOT NULL, api TEXT NOT NULL, endpoint TEXT NULL, "
        "   UNIQUE(node_id, api), FOREIGN KEY(node_id) REFERENCES nodes(id)"
        ");",
    ),
    
    (
        'node_failures',
        "CREATE TABLE node_failures ("
        "    node_id INTEGER NOT NULL, api TEXT NOT NULL, failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "    FOREIGN KEY(node_id) REFERENCES nodes(id)"
        ");",
    )
]


class BaseAdapter(GenericDBWrapper):
    @abstractmethod
    def begin_transaction(self, cursor):
        raise NotImplemented
    
    @abstractmethod
    def commit_transaction(self, cursor):
        raise NotImplemented
    
    @abstractmethod
    def rollback_transaction(self, cursor):
        raise NotImplemented


class SqliteAdapter(SqliteWrapper, BaseAdapter):
    DEFAULT_DB_FOLDER = expanduser('~/.privex_eos')
    """If an absolute path isn't given, store the sqlite3 database file in this folder"""
    
    DEFAULT_DB_NAME = 'privex_eos.db'
    """If no database is specified to :meth:`.__init__`, then use this (appended to :py:attr:`.DEFAULT_DB_FOLDER`)"""
    
    DEFAULT_DB = join(DEFAULT_DB_FOLDER, DEFAULT_DB_NAME)
    """
    Combined :py:attr:`.DEFAULT_DB_FOLDER` and :py:attr:`.DEFAULT_DB_NAME` used as default absolute path for
    the sqlite3 database used for storing information about RPC nodes
    """

    def begin_transaction(self, cursor):
        cursor.execute('BEGIN')
        return cursor

    def commit_transaction(self, cursor):
        cursor.execute('COMMIT')
        return cursor

    def rollback_transaction(self, cursor):
        cursor.execute('COMMIT')
        return cursor

    SCHEMAS: List[Tuple[str, str]] = SQLITE_SCHEMA

