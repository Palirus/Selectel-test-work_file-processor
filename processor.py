import asyncio, asyncssh
from queue import Queue

from db import Storage
from Error import EmptyReadFileException, ParseFileException
from workers import read_worker, send_worker, assigner
from config import config


async def processing_file(file_name: str, storage: Storage, send_data: Queue) -> None:
    await storage.set_file_in_db(file_name)
    start_line = await storage.get_last_line_file(file_name)
    print(f'\n Worker started processing the file "{file_name}" from the line numbered {start_line}')
    async with asyncssh.connect(
        "localhost", username="test", password="test", port=22, known_hosts=None
    ) as conn:
        while True:
            last_line_processing = await storage.get_last_line_file(file_name)
            try:
                data, end_line = await processing_lines(
                    conn, file_name, last_line_processing, CHANKSIZE_LINE
                )
                if data:
                    await send_data.put({file_name: (data, end_line)})
            except Exception as e:
                print("no write in the file", e)
            await asyncio.sleep(2)


async def awk_read(conn, file_name: str, start_line: int, CHANKSIZE_LINE: int) -> str:
    try:
        command = (
            f'awk -F " " \'NR>{start_line} && NR<={start_line+CHANKSIZE_LINE}'
            + "{arr[$1]+=$2}END{for (a in arr) print a, arr[a], NR}'"
            + f" {FILE_DIR}{file_name}"
        )

        awk = await conn.run(command, check=True, timeout=None)
        result = awk.stdout
        print(result)
        # print(awk)
    except asyncssh.ProcessError as e:
        print(f"ERROR awk_read: {e}")
        print(awk.stderr)
        result = None
        raise
    return result


async def processing_lines(conn, file_name, last_line_processing: int, CHANKSIZE_LINE: int) -> tuple[dict, int]:
    def get_end_line(EOF_line: int) -> int:
        interval_lines = last_line_processing + CHANKSIZE_LINE
        end_line = interval_lines if (EOF_line > interval_lines) else EOF_line
        return end_line

    data = {}
    agg_lines = await awk_read(conn, file_name, last_line_processing, CHANKSIZE_LINE)
    if agg_lines is None:
        raise EmptyReadFileException

    lines_list = list(filter(None, agg_lines.split("\n")))  # EMPTY STR
    print(f"last_line_processing: {last_line_processing},\n lines_list: {lines_list}")
    EOF_line = 0
    for line in lines_list:
        try:
            id, resourse, EOF_line = line.split(" ")
            data.update({id: resourse})
        except Exception as e:
            print("ParseFileException", e)
            raise ParseFileException
        print("EOF_line", EOF_line)
    end_line = get_end_line(int(EOF_line))
    return data, end_line


async def main(pool_size):
    storage = Storage(config())
    await storage.connect_pool()
    await storage.init_db()  # init db for first start

    queue_files = asyncio.Queue(10)
    send_data = asyncio.Queue(1000)
    read_workers = [
        asyncio.create_task(
            read_worker(queue_files, processing_file, send_data, storage)
        )
        for _ in range(pool_size)
    ]
    send_workers = [asyncio.create_task(send_worker(send_data, storage)) for _ in range(pool_size)]
    await asyncio.gather(assigner(queue_files, FILE_DIR), *read_workers, *send_workers)


if __name__ == "__main__":
    POOL_SIZE = 50
    FILE_DIR = "/app/files/"
    CHANKSIZE_LINE = 4

    asyncio.run(main(POOL_SIZE))
