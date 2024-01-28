class DbResult:
    complete: bool
    message: str

    def __init__(self, complete: bool, message: str) -> None:
        self.message = message
        self.complete = complete

