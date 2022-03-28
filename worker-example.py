import asyncio, multiprocessing, asyncssh, sys
from random import randint

async def some_work(n, delay):
    await asyncio.sleep(delay)
    return f'task {n} with delay: {delay} completed'

async def worker(tasks, results):
    # individual worker task (sometimes called consumer)
    # - sequentially process tasks as they come into the queue
    # and emit the results
    while True:
        n, d = await tasks.get()
        result = await some_work(n, d)
        await results.put(result)

async def assigner(tasks):
    files = []
    # come up with tasks dynamically and enqueue them for processing
    async with asyncssh.connect('localhost', username="test", password="test", port=22, known_hosts=None) as conn:
        task_n = 0
        while True:
            await asyncio.sleep(1)
            current_files = await conn.run('ls /app/files', check=True)
            current_files = str(current_files.stdout).split('\n')
            if set(files) != set(current_files):
                new_files = list(set(files) - set(current_files))
                files = current_files
            task_n+=1
            # print('files', files, end='') 
            await tasks.put((new_files, randint(5, 10)))

async def displayer(q):
    # show results of the tasks as they arrive
    while True:
        result = await q.get()
        print(result)

async def main(pool_size):
    tasks = asyncio.Queue(100)
    results = asyncio.Queue(100)
    workers = [asyncio.create_task(worker(tasks, results))
               for _ in range(pool_size)]
    await asyncio.gather(assigner(tasks), displayer(results), *workers)

if __name__ == '__main__':
    POOL_SIZE = 50
    asyncio.run(main(POOL_SIZE))