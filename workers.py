import asyncio, asyncssh
from queue import Queue



async def sender(send_data: Queue, storage) -> None:
    while True:
        status, file_name, data, end_line = await send_data.get()
        print(f"sender file: {file_name}")
        print("data, end_line", data, end_line)
        if status == 'Done':
            await storage.upload_data(end_line, file_name=file_name, data=data)
        if status == 'Fail':
            print('Fail', file_name)
            return
        await asyncio.sleep(2)


async def assigner(queue_files: Queue, file_path='/') -> None:
    async with asyncssh.connect("localhost", username="test", password="test", port=22, known_hosts=None) as conn:
        files = []
        while True:
            current_files = await conn.run("ls {}".format(file_path), check=True)
            current_files = list(filter(None, str(current_files.stdout).split("\n")))
            if set(files) != set(current_files):
                added_files = list(set(current_files) - set(files))
                deleted_files = list(set(files) - set(current_files))
                files = current_files
                for file in added_files:
                    await queue_files.put(file)
                for file in deleted_files:
                    print(f"deleted files {file}")
            await asyncio.sleep(2)
