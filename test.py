x= 0


class Bruh:
    def __init__(self) -> None:
        global x

        x += 1


a = Bruh()
print(x)
b = Bruh()
print(x)
