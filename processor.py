import asyncio, asyncssh
from queue import Queue

from db import Storage
from errors import EmptyReadFileException, ParseFileException
from workers import sender, assigner
from config import Config
import dataconf
from psycopg.conninfo import make_conninfo


async def read_worker(ssh_conf, queue_files: Queue, send_data: Queue, storage) -> None:
    while True:
        file_name = await queue_files.get()
        try:
            await storage.set_file_in_db(file_name)
            start_line = await storage.get_last_line_file(file_name)
            print(f'\n Worker started processing the file "{file_name}" from the line numbered {start_line}')

            async with asyncssh.connect(**ssh_conf) as conn:
                while True:
                    start_line = await storage.get_last_line_file(file_name)
                    print('start_line:', start_line)
                    try:
                        data, end_line = await processing_lines(
                            conn, file_name, start_line, CHANKSIZE_LINE
                        )
                        # print('data, end_line', data, end_line)
                        status = 'Done'
                    except Exception as e:
                        status = 'Fail'
                        data = {}
                        end_line = None
                        # print("no write in the file", e)
                    finally:
                        await send_data.put((status, file_name, data, end_line))
                        await asyncio.sleep(WORKER_SLEEP)
        except Exception as e:
            print('read_worker', e)
        await asyncio.sleep(WORKER_SLEEP)


async def processing_lines(conn, file_name: str, start_line: int, CHANKSIZE_LINE: int) -> tuple[dict, int]:
    """Обработка строк

    :param conn: объект-соединение ssh
    :type conn: _type_
    :param file_name: имя файла
    :type file_name: str
    :param start_line: последняя обработанная строка файла (из Хранилища)
    :type start_line: int
    :param CHANKSIZE_LINE: Размер чанка
    :type CHANKSIZE_LINE: int
    :return: Двнные клиентов и поледняя обработанная строка в файле
    :rtype: tuple[dict, int]
    """
    def get_end_line(EOF_line: int) -> int:
        """Получить последнюю обработанную строку

        :param EOF_line: Конец файла
        :type EOF_line: int
        :return: номер последней обаботанной строки
        :rtype: int
        """
        interval_lines = start_line + CHANKSIZE_LINE
        # Возвращаем номер строки EOF файла, если интервал ушёл дальше
        end_line = interval_lines if (EOF_line > interval_lines) else EOF_line
        return end_line

    def parse_line(line: str, delimeter: str = ' ') -> str:
        id, resourse, EOF_line = line.split(delimeter)
        return id, resourse, EOF_line

    data = {}
    agg_lines = await awk_read(conn, file_name, start_line, CHANKSIZE_LINE)
    # print('agg_lines', agg_lines)
    if agg_lines == "":
        raise EmptyReadFileException("EmptyReadFileException")
    print('agg_lines', agg_lines)

    lines_list = list(filter(None, agg_lines.split("\n")))  # EMPTY STR
    print(f"start_line: {start_line},\n lines_list: {lines_list}")
    for line in lines_list:
        try:
            id, resourse, EOF_line = parse_line(line)
            data.update({id: resourse})
        except Exception as e:
            print("ParseFileException", e)
            raise ParseFileException
        print("EOF_line", EOF_line)
    end_line = get_end_line(int(EOF_line))
    return data, end_line


async def awk_read(conn, file_name: str, start_line: int, CHANKSIZE_LINE: int) -> str:
    """Чтение файлов через утилиту awk

    :param conn: ssh соединение
    :type conn: _type_
    :param file_name: _description_
    :type file_name: str
    :param start_line: строка начала чтения
    :type start_line: int
    :param CHANKSIZE_LINE: чанк - количество строк при чтении
    :type CHANKSIZE_LINE: int
    :return: строка с результатом отработанного процесса awk
    :rtype: str
    """
    try:
        command = (
            f'awk -F " " \'NR>{start_line} && NR<={start_line+CHANKSIZE_LINE}'
            + "{arr[$1]+=$2}END{for (a in arr) print a, arr[a], NR}'"
            + f" {FILE_DIR}{file_name}"
        )

        awk = await conn.run(command, check=True, timeout=None)
        result = awk.stdout
        print('result:\n', result)
        # print(awk)
    except asyncssh.ProcessError as e:
        print(f"ERROR awk_read: {e}")
        print(awk.stderr)
        result = None
        raise
    return result


async def main(pool_size: int) -> None:
    conf = dataconf.file('config.hocon', Config)
    conninfo_postgres = make_conninfo(**conf.postgresql.__dict__)
    ssh_conf=conf.ssh.__dict__

    storage = Storage(conninfo_postgres)
    await storage.connect_pool()
    await storage.init_db()  # init db for first start

    queue_files = asyncio.Queue(QUEUE_FILES)
    send_data = asyncio.Queue(QUEUE_SEND_DATA)
    read_workers = [
        asyncio.create_task(
            read_worker(ssh_conf, queue_files, send_data, storage)
        )
        for _ in range(pool_size)
    ]
    senders = [asyncio.create_task(sender(send_data, storage)) for _ in range(pool_size)]
    await asyncio.gather(assigner(queue_files, FILE_DIR), *read_workers, *senders)


if __name__ == "__main__":
    POOL_SIZE = 50
    FILE_DIR = "/app/files/"
    CHANKSIZE_LINE = 4
    QUEUE_FILES = 10
    QUEUE_SEND_DATA = 100
    WORKER_SLEEP = 3

    asyncio.run(main(POOL_SIZE))
