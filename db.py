#!/usr/bin/python
from psycopg2 import OperationalError, errorcodes, errors, connect


class Storage:

    def __init__(self, config) -> None:
        self.conn = None
        self.config = config


    def connect(self):
        """ connect to the PostgreSQL database server """
        try:
            if self.conn is not None:
                self.conn.close()
            print('connecting to the PostgreSQL database...')
            self.conn = connect(**self.config)
            self.conn.autocommit = True
        except OperationalError as err:
            # pass exception to function
            print(err)

            # set the connection to 'None' in case of error
            conn = None


    def run_query(self, query: str, param:list = ()):
        try:
            with self.conn as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, param)
                    record = cursor.fetchall()
                    return record
        except Exception as e:
            print(e)


    def ping(self):
        try:
            with self.conn:
                with self.conn.cursor() as cursor:
                    cursor.execute('SELECT version()')
                    # print(cursor.fetchall())
        except Exception as e:
            print(e)
            print('Not set connection')
            raise


if __name__ == '__main__':
    from config import config

    s =Storage(config())
    # s.ping()
    res = s.run_query('select 1')
    print(res)

