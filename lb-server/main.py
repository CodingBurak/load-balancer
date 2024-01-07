import argparse
import asyncio
import uuid
from pprint import pprint
from random import randint

from LoadBalancerAlgorithm import Algorithms, LoadBalancerAlgo, RoundRobin, Server

import aiohttp
from aiohttp import web, ClientError

routes = web.RouteTableDef()

ports = []
BASE_URL = ""
DEFAULT_BASE_URL = "http://localhost"
health = "/health"
lb_algo: LoadBalancerAlgo | None = None

lock = asyncio.Lock()


@routes.get('/')
async def ping(request):
    counter = uuid.uuid4()
    # async with lock:
    async with aiohttp.ClientSession(trust_env=True) as session:
        server = lb_algo.get_next_server()
        print(f"for peer {request.transport.get_extra_info('peername')} "
              f" current server {lb_algo.index} id {counter}")
        if server:
            async with session.get(f"{server.host}:{server.port}") as resp:
                data = await resp.text()
                # this will always print the last lb_algo_index for the moment we get a response from session.get
                # print(f"finished server {server.to_dict()} current server {lb_algo.index} id {counter}")
                # in order to get the number we can use asyncio.Lock to lock the critical section, this will lead to a sequential

                print(f"finished server {server.to_dict()} current server {lb_algo.index} id {counter}")
                return web.Response(status=resp.status, text=data)


def create_servers() -> list[Server]:
    return [Server(BASE_URL if BASE_URL else DEFAULT_BASE_URL, port, False) for port in ports]


async def get_health(server: Server):
    """
    This sets up a get_health tasks, which access and modify the lb_algo concurrently.
    It demonstrates the use of locks to protect access to the shared resource (lb_algo)
     and ensures thread safety when multiple tasks try to modify it concurrently.

    :param server: server we want to do healthcheck
    :return:
    """
    print(f"running healtchheck for {server.host, server.port, server.healthy}")
    async with aiohttp.ClientSession(trust_env=True) as session:
        try:
            async with session.get(f"{server.host}:{server.port}{health}") as resp:
                data = await resp.text()
                server.healthy = True
                async with lock:
                    lb_algo.add_server(server)
                print(f"success healthy? {lb_algo.get_healthy_servers()}")
                print(f"success all servers? {lb_algo.servers}")
                return web.Response(status=resp.status, text=data)
        except ClientError as ce:
            print(f"client error removing server f {server.host, server.port, server.healthy}")
            async with lock:
                server.healthy = False
                lb_algo.remove_server(server)


async def start_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost')
    await site.start()


async def main():
    # run initial tasks
    tasks = [asyncio.create_task(get_health(server)) for server in server_candidates]
    await asyncio.gather(*tasks)
    [task.cancel() for task in tasks]


async def run_healthchecks(once=False):
    while True:
        # Call the get_health function here for each server
        for server in server_candidates:
            await get_health(server)
        if not once:
            # do it periodically
            await asyncio.sleep(5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="give the ports and baseulr of the running servers")
    parser.add_argument("-port_servers", nargs='+', type=int, help="Ports of backend servers")
    parser.add_argument("-base_url", type=str, help="base url of backend servers")
    parser.add_argument("-algo", type=str, help="pick between roundrobin")
    args = parser.parse_args()
    ports = args.port_servers
    BASE_URL = args.base_url
    algo = args.algo if args.algo else Algorithms.ROUND_ROBIN
    server_candidates = create_servers()
    if algo == Algorithms.ROUND_ROBIN:
        lb_algo = RoundRobin(server_candidates)
    pprint(f"{ports=} {BASE_URL=}")
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.create_task(run_healthchecks(once=False))
    loop.create_task(start_server())
    loop.run_forever()
