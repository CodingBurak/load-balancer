from abc import abstractmethod, ABC
from dataclasses import dataclass, asdict

from enum import StrEnum

class Algorithms(StrEnum):
    ROUND_ROBIN = 'roundrobin'


@dataclass(slots=True)
class Server:
    host: str
    port: int
    healthy: bool = False

    def to_dict(self):
        return asdict(self)

    def __eq__(self, item: 'Server'):
        # we explicitly want to check the health checks
        return (
                self.port == item.port and
                self.host == item.host)


class LoadBalancerAlgo(ABC):

    def __init__(self, servers: list):
        self.servers: list[Server] = servers

    @abstractmethod
    def get_server(self) -> Server:
        pass

    @abstractmethod
    def get_next_server(self) -> Server:
        pass

    def set_servers(self, servers: list[Server]) -> None:
        self.servers = servers

    def add_server(self, server: Server):
        print(f"add server server: {server}")
        if server not in self.servers:
            self.servers.append(server)
        elif server.healthy != self.servers[self.servers.index(server)].healthy:
            self.servers[self.servers.index(server)].healthy = server.healthy

    def remove_server(self, server):
        try:
            self.servers[self.servers.index(server)].healthy = server.healthy
        except ValueError:
            pass

    def get_healthy_servers(self):
        return [server for server in self.servers if server.healthy]


class RoundRobin(LoadBalancerAlgo):
    index = 0

    def __init__(self, servers):
        super().__init__(servers)

    def get_next_server(self) -> Server:
        self.index += 1
        self.index %= len(self.get_healthy_servers())
        return self.get_server()

    def get_server(self) -> Server:
        return self.get_healthy_servers()[self.index] if len(self.get_healthy_servers()) else []
