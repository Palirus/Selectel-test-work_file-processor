import asyncio, asyncssh
from queue import Queue


async def read_worker(queue_files: Queue, processing_file: object, send_data: Queue, storage) -> None:
    while True:
        try:
            file_name = await queue_files.get()
            await processing_file(file_name, storage, send_data)
        except Exception as e:
            print("Error when read file", e)

async def send_worker(send_data: Queue, storage) -> None:
    while True:
        message = await send_data.get()
        file_name = list(message.keys()).pop()
        data, end_line = message[file_name]
        print("send_worker", message)
        print("data, end_line", data, end_line)
        await storage.upload_data(end_line, file_name=file_name, data=data)
        await asyncio.sleep(2)

async def assigner(queue_files: Queue, file_path='/') -> None:
    async with asyncssh.connect( "localhost", username="test", password="test", port=22, known_hosts=None) as conn:
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
