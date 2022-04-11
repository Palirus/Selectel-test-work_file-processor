import asyncio
from typing import Any
from psycopg import OperationalError, cursor
from psycopg_pool import ConnectionPool


class DataBase:
    def __init__(self, config: dict) -> None:
        self.pool = None
        self.config = config

    async def connect_pool(self):
        try:
            if self.pool is not None:
                self.pool.close()
            print("connecting pool to the PostgreSQL database...")
            self.pool = ConnectionPool(
                "host= storage dbname=storage user=user password=password"
            )
        except OperationalError as err:
            print("Pool error:", err)

    async def run_query(self, query: str, param: tuple = ()) -> cursor:
        try:
            with self.pool.connection() as coon:
                cur = coon.execute(query, param)
                coon.commit()
                # print(f"statusmessage: {cur.statusmessage}")
                return cur
        except Exception as e:
            print(e)

    async def ping(self):
        try:
            await self.connect_pool()
            with self.pool.connection() as conn:
                conn.autocommit = True
                cur = conn.execute("SELECT version()")
                print(cur.fetchall())
        except Exception as e:
            print("Not set connection", e)
            raise


class Storage(DataBase):
    def __init__(self, config: dict) -> None:
        super()
        self.pool = None
        self.config = config

    async def get_file_in_db(self, file_name) -> list[tuple[Any, ...]]:
        cursor = await self.run_query(
            "SELECT * FROM files WHERE name = %s;", (file_name,)
        )
        return cursor.fetchall()

    async def set_file_in_db(self, file_name) -> None:
        row = await self.get_file_in_db(file_name)
        if not row:
            await self.run_query("INSERT INTO files VALUES (%s, 0);", (file_name,))
            print("Set file in db")

    async def set_customer_in_db(self, id: int) -> int:
        row = await self.get_file_in_db(id)
        if not row:
            await self.run_query("INSERT INTO customer VALUES (%s, 0);", (id,))
            print(f"Set with id:{id} customer in db")

    async def get_last_line_file(self, file_name: str) -> int:
        try:
            data = await self.get_file_in_db(file_name)
            if data:
                start_line = int(data[0][1])
            else:
                start_line = 0
            return start_line
        except Exception as e:
            print("Error parse last line of file from db:", e)

    async def get_customer_in_db(self, id: int) -> list[tuple[Any, ...]]:
        cursor = await self.run_query("SELECT * FROM customer WHERE id = %s;", (id,))
        return cursor.fetchall()

    async def upload_data(self, end_line, data=None, file_name=None) -> None:
        try:
            with self.pool.connection() as conn:
                conn.execute(
                    """UPDATE files SET LAST_ROW_PROCESSING= %s 
                                WHERE name= %s;""",
                    (end_line, file_name),
                )
                for id, count in data.items():
                    await self.set_customer_in_db(id)
                    conn.execute(
                        """UPDATE customer SET COUNT=COUNT+%s
                                    WHERE id=%s;""",
                        (count, id),
                    )
                conn.commit()
        except Exception as e:
            print("Send data is fail", e)
            raise

    async def init_db(self) -> None:
        await self.run_query(
            """CREATE TABLE IF NOT EXISTS customer
                (ID INT PRIMARY KEY     NOT NULL,
                COUNT INT               NOT NULL); """
        )
        query = await self.run_query(
            """CREATE TABLE IF NOT EXISTS files
                (NAME TEXT PRIMARY KEY     NOT NULL,
                LAST_ROW_PROCESSING INT    DEFAULT 0); """
        )
        print(query.statusmessage)


async def main():
    from config import config

    storage = Storage(config())
    await storage.ping()


if __name__ == "__main__":
    asyncio.run(main())
