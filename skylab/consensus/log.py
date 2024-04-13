class Log:
    def __init__(self, term: int, command: str):
        self.term = term
        self.command = command

    def exec(self):
        ...

    def encode(self) -> dict:
        return {'term': self.term,
                'command': self.command}


def decode_log(log: dict) -> Log:
    return Log(
        term=log.get('term') or log['log_term'],
        command=log['command']
    )
