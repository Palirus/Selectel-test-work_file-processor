import asyncio, asyncssh, sys, aiofiles
from typing import cast

async def handle_client(process: asyncssh.SSHServerProcess):
    channel = cast(asyncssh.SSHLineEditorChannel, process.channel)

    process.stdout.write('Welcome to my SSH server, %s!\n\n' %
                         process.get_extra_info('username'))

    channel.set_echo(False)
    process.stdout.write('Tell me a secret: ')
    secret = await process.stdin.readline()

    channel.set_line_mode(False)
    process.stdout.write('\nYour secret is safe with me! '
                         'Press any key to exit...')
    await process.stdin.read(1)

    process.stdout.write('\n')
    process.exit(0)

async def start_server() -> None:
    await asyncssh.listen('', 8022, server_host_keys=['ssh_host_key'],
                          authorized_client_keys='ssh_user_ca',
                          process_factory=handle_client)

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(start_server())
except (OSError, asyncssh.Error) as exc:
    sys.exit('Error starting server: ' + str(exc))

loop.run_forever()