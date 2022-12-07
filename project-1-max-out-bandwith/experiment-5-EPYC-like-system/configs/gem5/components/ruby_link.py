from m5.objects import SimpleIntLink, SimpleExtLink

class IntLink(SimpleIntLink):
    _link_id = 0

    @classmethod
    def _get_link_id(cls):
        cls._link_id += 1
        return cls._link_id - 1

    def __init__(self):
        super().__init__()
        self.link_id = self._get_link_id()

class ExtLink(SimpleExtLink):
    _link_id = 0

    @classmethod
    def _get_link_id(cls):
        cls._link_id += 1
        return cls._link_id - 1

    def __init__(self):
        super().__init__()
        self.link_id = self._get_link_id()
