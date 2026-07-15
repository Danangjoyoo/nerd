_values: list[str] = []


def snapshot(value: str) -> tuple[str, ...]:
    _values.append(value)
    return tuple(_values)
