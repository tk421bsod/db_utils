import asyncio
import logging

import aiomysql

class async_db:
    __slots__ = ("ip", "database", "TABLES", "logger", "failed", "pool", "p", "user")

    def __init__(self, user, password, ip, database, tables=None):
        """
        Parameters
        ----------
        user : str
            User to connect as.
        password : str
            The database password.
        ip : str
            The IP address to use for the database. Defaults to 'localhost'.
        database : str
            The name of the database to connect to.
        tables : dict
        """
        self.p = password
        if not ip:
            ip = "localhost"
        self.ip = ip
        self.database = database
        self.TABLES = tables
        self.logger = logging.getLogger(__name__)
        self.user = user
        self.failed = False
        self.logger.debug("Database API initialized.")

    def requires_connection(func):
        async def requires_connection_inner(self, *args, **kwargs):
            """Handles connection acquisition for functions that require it"""
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    self.logger.debug(f"Calling {func.__name__} with {args}")
                    return await func(self, cur, *args, **kwargs)
        return requires_connection_inner

    @requires_connection
    async def ensure_tables(self, cur):
        self.logger.info("Finishing database setup...")
        for table, schema in self.TABLES.items():
            ret = await cur.execute(f"show tables like '{table}'")
            if not ret:
                self.logger.debug(f'Table {self.database}.{table} doesn\'t exist. Creating it.')
                self.logger.debug(f"Schema for this table is {schema}")
                await cur.execute(f'create table {table}({schema})')
                if not self.failed:
                    self.failed = True
        if not self.failed:
            self.logger.info('Database setup was already finished, nothing to do')
        else:
            self.logger.warning('Database setup finished.')
        del self.TABLES

    async def connect(self):
        self.logger.info(f"Attempting to connect to database '{self.database}' on '{self.ip}'...")
        self.pool = await aiomysql.create_pool(host=self.ip, user=self.user, password=self.p, db=self.database, charset='utf8mb4', cursorclass=aiomysql.cursors.DictCursor, autocommit=True)

    @requires_connection
    async def exec(self, cur, query, params):
        """Executes 'query' with 'params'. Uses aiomysql's parameterized queries.

        Parameters
        ----------
        query : str
            The SQL query to execute. 

        params : tuple
            The parameters for the query. Must be provided but can be empty.
        """
        await cur.execute(str(query), params)
        row = await cur.fetchall()
        return row if row != () and row != "()" else None
