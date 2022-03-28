#!/usr/bin/python
import psycopg2


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
            self.conn = psycopg2.connect(**self.config)
        except Exception as error:
            print(error)
            raise

    def run_query(self, query: str):
        def validate(query: str):
            pass
            # raise Exception('bad sql')

        try:
            self.ping()
        except Exception:
            self.connect()   

        try:
            validate(query)
            with self.conn.cursor() as cursor:
                self.conn.autocommit = True
                cursor.execute(query)
                record = cursor.fetchall()
                return record
        except psycopg2.DatabaseError as e:
            print(e)
        except Exception as e:
            print(e)
            raise

    def ping(self):
        try:
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

