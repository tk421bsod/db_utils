import logging
import pymysql

class db:
    def __init__(self, user, password, ip, database, tables=None):
        self.p = password
        if not ip:
            ip = "localhost"
        self.TABLES = tables
        self.ip = ip
        self.database = database
        self.failed = False
        self.logger = logging.getLogger(name=f'db')
        self.user = user
        self.conn = self.attempt_connection()
        self.logger.info("Connected to database.")

    def requires_connection(func):
        def requires_connection_inner(self, *args, **kwargs):
            """Attempts a reconnect if OperationalError is raised"""
            try:
                self.logger.info(f"Calling {func.__name__} with {args}")
                return func(self, *args, **kwargs)
            except (pymysql.err.OperationalError, pymysql.err.InterfaceError) as e:
                self.logger.info("db connection lost, reconnecting")
                self.reconnect()
                return func(self, *args, **kwargs)
        return requires_connection_inner

    @requires_connection
    def ensure_tables(self):
        self.logger.info("Finishing database setup...")
        for table, schema in self.TABLES.items():
            ret = self.conn.execute(f"show tables like '{table}'")
            if not ret:
                self.logger.debug(f'Table {self.database}.{table} doesn\'t exist. Creating it.')
                self.logger.debug(f"Schema for this table is {schema}")
                self.conn.execute(f'create table {table}({schema})')
                if not self.failed:
                    self.failed = True
        if not self.failed:
            self.logger.info('Database setup was already finished, nothing to do')
        else:
            self.logger.warning('Database setup finished.')

    def attempt_connection(self):
        self.logger.info(f"Attempting to connect to database '{self.database}' on '{self.ip}'...")
        return self.connect()

    def reconnect(self):
        self.conn = self.connect()

    def connect(self):
        conn = pymysql.connect(host=self.ip,
                    user=self.user,
                    password=self.p,
                    db=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True).cursor()
        return conn

    @requires_connection
    def exec(self, query, params):
        """
        Executes 'query' with 'params'. Uses pymysql's parameterized queries.
        Uses legacy (pre Maximilian v1.2) exec behavior - will not always return iterables

        Parameters
        ----------
        query : str
            The SQL query to execute. 

        params : tuple
            The parameters to pass to the query. Must be provided but can be empty.
        """
        self.conn.execute(str(query), params)
        row = self.conn.fetchall()
        if len(row) == 1:
            row = row[0]
        return row if row != () and row != "()" else None
