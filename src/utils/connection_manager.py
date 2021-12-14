from crate import client
from crate.client.sqlalchemy.dialect import CrateDialect
import sqlalchemy.pool as pool
import argparse
from sqlalchemy import create_engine

class ConnectionManager():
    """
    Invoke queries to database in parallel.
    """

    def __init__(self, connection, query):
        self.connection = connection
        self.query = query

    def querydb_dbapi(connection, query):
        """
        Submit query to database.
        """
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        return result

    def querydb_sqlalchemy(connection, query):
        """
        Submit query to database.
        """
        result = connection.execute(query).fetchone()
        return result

    def set_connection(self, db, connection):
        self.connection[db] = connection

    def get_connection(connection):
        parser = argparse.ArgumentParser()
        parser.add_argument('--driver')
        parser.add_argument('--pool', action='store_true')
        args = parser.parse_args()

        if args.driver == "dbapi":
        # Use DBAPI driver.
            if args.pool:
                query = querydb_dbapi
                # Use a connection pool matching the number of workers.
                engine  = create_engine("crate://localhost:4200", connect_args={"pool_size": 10})
            else:
                # Don't use a pool.
                engine = create_engine("crate://localhost:4200")
        elif args.driver == "sqlalchemy":
            if args.pool:
                query = querydb_sqlalchemy
                # Use a connection pool matching the number of workers.
                engine = create_engine("crate://localhost:4200", connect_args={"pool_size": 10})
            else:
                # Don't use a pool.
                engine = create_engine("crate://localhost:4200")
            connection = engine.connect()
        else:
            raise ValueError("Unknown value for --driver: Use 'dbapi' or 'sqlalchemy'.")

    # Invoke some database queries.
    query = 'SELECT 1;'

if __name__ == '__main__':
    main()
