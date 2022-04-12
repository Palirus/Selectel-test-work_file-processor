from dataclasses import astuple, dataclass, field, asdict
from typing import List, Dict, Text, Union, Optional


class AbstractBaseClass:
    pass

@dataclass
class Postgresql(AbstractBaseClass):
    host: Text
    dbname: Text
    user: Text
    password: Text

    def __iter__(self):
        return iter(asdict(self))


@dataclass
class SSH:
    host: Text
    port: int
    username: Text
    password: Text
    known_hosts: Optional[bool]

    def __iter__(self):
        return iter(asdict(self))


@dataclass
class Config:
    postgresql: Postgresql
    ssh: Optional[SSH]

    def __iter__(self):
        return iter(asdict(self))
