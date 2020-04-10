from dataclasses import dataclass, fields
from operator import attrgetter
from typing import Dict


@dataclass
class AuthData:
    email: str

    @classmethod
    def from_jwt_payload(cls, payload: Dict[str, str]):
        dataclass_fields = list(map(attrgetter("name"), fields(cls)))
        attrs = {field: value for field, value in payload.items()
                 if field in dataclass_fields}
        return cls(**attrs)


@dataclass
class ExchangeData:
    name: str
    type: str = "fanout"
    routing_key: str = ""
