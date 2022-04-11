from curses import noecho
from distutils.command.upload import upload
import os, subprocess
import asyncio, multiprocessing, asyncssh, sys
from turtle import end_fill
from shutil import ExecError
from time import sleep

from db import Storage, DataBase
from workers import read_worker, send_worker, assigner
from config import config

FILE_DIR='/app/files/'

# storage.ping()




# work_dir = '/Users/artem/test-task-processor-generator/files/'


# asyncssh.connect('localhost', username="test", password="test", port=22, known_hosts=None)


async def run_client():
    async with asyncssh.connect('localhost', username="test", password="test", port=22, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            async with sftp.open('/app/files/test1.txt') as f:
                while True:
                    lines = await f.read(100)
                    if lines:
                        print(lines, type(lines))
                        await asyncio.sleep(4)
                    # if lines is not None:
                    #     print('lines:', lines)

                # tell_res = await f.tell()
                # print(tell_res)

                # seek_res = await f.seek(1)
                # print(seek_res)

                # tell_res = await f.tell()
                # print(tell_res)

        # while True:
            # result = await conn.run('cat /app/files/test1.txt', check=True)
            # print(result.stdout, end='')

        # async with aiofiles.open('filename', mode='r') as f:
        #     contents = await f.read()
        # print(contents)

# asyncssh.SSHClientConnection.run
CHANKSIZE_LINE=4
# try:
#     asyncio.get_event_loop().run_until_complete(run_client())
# except (OSError, asyncssh.Error) as exc:
#     sys.exit('SSH connection failed: ' + str(exc))
async def processing_file(file_name, storage, send_data):
    async def check_writing_file():
        data = await storage.set_file_in_db()
        if data:
            start_line = int(data[0][1])
        else:
            start_line = 0
        awk = await conn.run(f"awk -F \" \" 'NR>{start_line} && NR<{start_line + CHANKSIZE_LINE}" + "{arr[$1]+=$2}END{for (a in arr) print a, arr[a], NR}' /app/files/test1.txt", check=True, timeout=None)
        print(f"awk: {awk}")
        if not awk.stdout:
            return False
        else:
            return True
            
    # MAIN
    await storage.set_file_in_db(file_name)
    start_line = await storage.get_last_line_file(file_name)
    print(f'\n worker start processing "{file_name}" at {start_line} line')
    async with asyncssh.connect('localhost', username="test", password="test", port=22, known_hosts=None) as conn:
        while True:
            last_line_processing = await storage.get_last_line_file(file_name)
            try:
                data, end_line = await processing_lines(conn, file_name, last_line_processing, CHANKSIZE_LINE)
                if data:
                    await send_data.put({file_name:(data, end_line)})
            except Exception as e:
                print('no write in the file', e)
            await asyncio.sleep(2)



async def awk_read(conn, file_name, start_line, CHANKSIZE_LINE):
    try:
        # awk -F " " 'NR>0 && NR<100 {arr[$1]+=$2}END{for (a in arr) print a, arr[a]}' files/test1.txt
        command = f"awk -F \" \" 'NR>{start_line} && NR<={start_line+CHANKSIZE_LINE}" + "{arr[$1]+=$2}END{for (a in arr) print a, arr[a], NR}'" + f" {FILE_DIR}{file_name}"
        # print(f"command: {command}")
        awk = await conn.run(f"awk -F \" \" 'NR>{start_line} && NR<={start_line+CHANKSIZE_LINE}" + "{arr[$1]+=$2}END{for (a in arr) print a, arr[a], NR}'" + f" {FILE_DIR}{file_name}", check=True, timeout=None)
        # print('awk_read', awk)
        result = awk.stdout
    except asyncssh.ProcessError as e:
        print(f'ERROR awk_read: {e}')
        print(awk.stderr)
        result = None
        raise
    finally:
        return result

async def processing_lines(conn, file_name, last_line_processing: int, CHANKSIZE_LINE: int):
    def get_end_line(EOF_line: int):
        interval_lines = last_line_processing + CHANKSIZE_LINE
        end_line = interval_lines if (EOF_line > interval_lines) else EOF_line
        return end_line
    
    data = {}
    agg_lines = await awk_read(conn, file_name, last_line_processing, CHANKSIZE_LINE)
    if agg_lines is None:
        raise ReadFileException

    lines_list = list(filter(None, agg_lines.split('\n'))) # EMPTY STR
    print(f'last_line_processing: {last_line_processing},\n lines_list: {lines_list}')
    EOF_line=0
    for line in lines_list:
        try:
            id, resourse, EOF_line = line.split(' ')
            data.update({id:resourse})
        except Exception as e:
            print("ParseFileException", e)
            raise ParseFileException
        print('EOF_line', EOF_line)
    end_line = get_end_line(int(EOF_line))
    return data, end_line


class ReadFileException(Exception):
    def __init__(self, message: str = "Error reading file") -> None:
        self.message = message
        super().__init__(self.message)

class ParseFileException(Exception):
    def __init__(self, message: str = "Error parse file") -> None:
        self.message = message
        super().__init__(self.message)
    


async def main(pool_size):
    storage = Storage(config())
    await storage.connect_pool()
    # await init_storage(storage)


    queue_files = asyncio.Queue(10)
    send_data = asyncio.Queue(1000)
    read_workers = [asyncio.create_task(read_worker(queue_files, processing_file, send_data, storage))
                        for _ in range(pool_size)]
    send_workers = [asyncio.create_task(send_worker(send_data, storage))
                        for _ in range(pool_size)]
    await asyncio.gather(assigner(queue_files), *read_workers, *send_workers)

if __name__ == '__main__':
    POOL_SIZE = 50
    asyncio.run(main(POOL_SIZE))

# async def main():
#     tasks = asyncio.Queue(20)
#     await asyncio.gather(assigner(tasks), worker(tasks))
