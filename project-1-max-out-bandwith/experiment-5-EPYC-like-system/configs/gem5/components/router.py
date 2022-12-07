from m5.objects import Switch

class Router(Switch):
    _router_id = 0

    @classmethod
    def _get_router_id(cls):
        cls._router_id += 1
        return cls._router_id - 1
    
    def __init__(self):
        super().__init__()
        self.router_id = self._get_router_id()
