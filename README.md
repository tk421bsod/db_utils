# db_utils
Synchronous and asynchronous implementations of a simple API for interaction with a MySQL database.
  
## usage
Ensure that you have:
- A properly configured and running MySQL / MariaDB database server
- Python3.8+
- `pymysql` installed (required by both db and async_db)
- `aiomysql` installed (required by async_db)

In your application, import the class you need and instantiate it, passing it:
- The name of the user you want to connect as
- Password in plain text
- IP address of the server (can be localhost)
- Name of the database to connect to 
- (optional) A map of table names to schemas e.g {"user_ids":"id bigint"}. Required if using `ensure_tables`.  
  
Use `async_db` if possible. It includes several optimizations and is more performant and reliable than `db`.
  
`db` immediately attempts a connection to the server on instance creation.  
`async_db` does not do this to avoid blocking. You'll need to `await` `<instance>.connect()` before doing anything.  
  
Both classes can throw pymysql.err.OperationalError if they fail to connect.  
  
You may want to ensure that all required tables are present before trying to perform queries.  
Fortunately both classes provide a utility to do just that.  
Just run `<instance>.ensure_tables()` to create tables if needed.  
  
To perform queries, just call `<instance>.exec()` and pass it your query and any parameters.  
Parameters are represented by `%s` in queries and are passed as a tuple to `exec`.  
If your query doesn't require parameters, pass an empty tuple.  
  
Using `async_db`? Queries always return a list of dicts.  
Using `db`? Queries return a list of dicts, but can sometimes return a dict by itself.  
These dicts follow the format `{"column_name":"value"}`.  
