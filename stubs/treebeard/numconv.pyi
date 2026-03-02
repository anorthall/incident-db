__version__: str
BASE85: str
BASE16: str
BASE32: str
BASE32HEX: str
BASE64: str
BASE64URL: str
BASE62: str

class NumConv:
    radix: int
    alphabet: str
    cached_map: dict[str, int]

    def __init__(self, radix: int = 10, alphabet: str = ...) -> None: ...
    def int2str(self, num: int) -> str: ...
    def str2int(self, num: str) -> int: ...

def int2str(num: int, radix: int = 10, alphabet: str = ...) -> str: ...
def str2int(num: str, radix: int = 10, alphabet: str = ...) -> int: ...
