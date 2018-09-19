
def main(data) -> int:
    print("main", "main 2", data)
    return 0


def can(data):
    return data


class Abc:
    def __init__(self):
        pass

    def __add__(self, other: int):
        return other + 2

    def __bool__(self):
        return False

    def ddd(self):
        return """abc"""
        pass

    def _dd(self):
        return 0

    def __d(self):
        return 0.0
