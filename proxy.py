from singleton import Singleton


class Proxy(metaclass=Singleton):
    schema = "socks5"
    user = "socks_user"
    password = "0c1a2375a0fe6d6934f3266779d4e316dc8933f81143ad"
    host = "a4a33997-6881-45de-8b63-014aa75d9afe.hsvc.ir"
    port = 30164
    # host = "16ab8291-0502-4752-a073-894c40d04ece.hsvc.ir"
    # port = 30968
    # host = "2fff21a8-0a99-49c7-bab4-0c188d59ca36.hsvc.ir"
    # port = 30677

    def __init__(self):
        self.addr = (
            f"{self.schema}://{self.user}:{self.password}@{self.host}:{self.port}"
        )
        # self.addr = "https://socks.liara.run"
        self.addr = "http://localhost:8082"

    @property
    def proxy(self):
        return {"http": self.addr, "https": self.addr}
