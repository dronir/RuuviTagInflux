from typing import List, Callable, Optional, Any

class RuuviTagSensor:
    @staticmethod
    def get_datas(callback: Callable, macs: Optional[List[str]] = ...) -> None: ...
