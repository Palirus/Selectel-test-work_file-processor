from distutils.command.upload import upload
import os
import asyncio, multiprocessing, asyncssh, sys
from shutil import ExecError
from time import sleep

from db import Storage
from config import config

FILE_DIR='/app/files/'

# db.ping()
def init_db(db):
    db.run_query('''CREATE TABLE IF NOT EXISTS customer
            (ID INT PRIMARY KEY     NOT NULL,
            COUNT           INT    NOT NULL); ''')
    r = db.run_query('''CREATE TABLE IF NOT EXISTS files
            (ID INT PRIMARY KEY     NOT NULL,
            name TEXT                NOT NULL,
            LAST_ROW_PROCESSING           INT    NOT NULL); ''')

    r = db.run_query('''select 1''')
    print(r)

db = Storage(config())
# init_db(db)



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

# try:
#     asyncio.get_event_loop().run_until_complete(run_client())
# except (OSError, asyncssh.Error) as exc:
#     sys.exit('SSH connection failed: ' + str(exc))
async def read_file(new_file):
    print('\n worker got new_file:', new_file)
    async with asyncssh.connect('localhost', username="test", password="test", port=22, known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            async with sftp.open(f'{FILE_DIR}{new_file}') as f:
                while True:
                    # lines = await f.read(offset)
                    lines = await f.read(4)
                    last_read_row = await f.tell()
                    data = await processing_lines(lines)
                    # await upload_data(data, last_read_row)
                    await asyncio.sleep(2)

async def processing_lines(lines):
    data = {}
    lines = list(filter(None, lines.split('\n')))
    for line in  lines:
        print(line)
        try:
            id, resourse = line.split(' ')
        except Exception as e:
            print(e)
        data.update({id:resourse})
    print(data, type(lines))
    return data

# async def upload_data(data):
#     db.run_query(f'''UPDATE IF NOT EXISTS files
#             SET LAST_ROW_PROCESSING={number_count}
#             WHERE name={name_file}; ''')

async def worker(tasks):
    while True:
        new_file = await tasks.get()
        await read_file(new_file)
        # await results.put(result)   

async def assigner(task):
    async with asyncssh.connect('localhost', username="test", password="test", port=22, known_hosts=None) as conn:
        files = []
        while True:
            await asyncio.sleep(2)
            current_files = await conn.run('ls /app/files', check=True)
            current_files = list(filter(None, str(current_files.stdout).split('\n')))
            # print(current_files.stdout, end='')
            # print(current_files, end='') 
            if set(files) != set(current_files):
                added_files = list(set(current_files) - set(files))
                deleted_files = list(set(files) - set(current_files))
                # print(set(files) != set(current_files), set(current_files) ^ set(files), 'current_files', current_files, '\nfiles', files, '\nnew_files:', new_files, end='') 
                files = current_files
                for file in added_files:
                    await task.put(file)
                for file in deleted_files:
                    print(f"deleted files {file}")
                # await task.put(new_files)
            # except:
            #     print('errrr')
            #     await asyncio.sleep(2)



async def main(pool_size):
    tasks = asyncio.Queue(100)
    workers = [asyncio.create_task(worker(tasks))
               for _ in range(pool_size)]
    await asyncio.gather(assigner(tasks), *workers)

if __name__ == '__main__':
    POOL_SIZE = 50
    asyncio.run(main(POOL_SIZE))

# async def main():
#     tasks = asyncio.Queue(20)
#     await asyncio.gather(assigner(tasks), worker(tasks))
