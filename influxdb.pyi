from typing import Optional, MutableMapping, Any, List

class InfluxDBClient:
    def __init__(self,
                 host: Optional[str],
                 port: Optional[int],
                 username: Optional[str],
                 password: Optional[str],
                 ssl: Optional[bool],
                 verify_ssl: Optional[bool]): ...

    def switch_database(self, db: str) -> None: ...

    def write_points(self, points: List[MutableMapping[str, Any]]) -> None: ...
