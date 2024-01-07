import argparse
import asyncio

from aiohttp import web
from aiohttp.web_request import Request

routes = web.RouteTableDef()
starting_port = 9000

server_list = []


def get_response(port):
    return """<!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <title>Index Page</title>
          </head>
          <body>
            Hello from the web server running at on port {port}.
          </body>
        </html>""".format(port=port)


@routes.get('/')
async def ping(request: Request):
    _, port = request.transport.get_extra_info('sockname')
    return web.Response(text=get_response(port),
                        content_type="text/html")

@routes.get('/health')
async def health(request: Request):
    print("health endpoint called")
    return web.Response(status=200, text="healthy")


async def start_server(port):
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner=runner, host='0.0.0.0', port=port)
    await site.start()
    # app.router.add_get('/', handle_request)
    print(f"Aiohttp server started on http://0.0.0.0:{port}")
    return site


async def main(amount_server: int):
    ports = range(starting_port, amount_server + starting_port)
    startup_tasks = []
    for port in ports:
        startup_tasks.append(start_server(port))
        # await start_server(port)
    await asyncio.gather(*startup_tasks)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run multiple aiohttp servers")
    parser.add_argument("num_servers", type=int, help="Number of aiohttp servers to create")
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.num_servers))
    loop.run_forever()
