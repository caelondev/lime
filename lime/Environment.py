from llvmlite import ir


class Environment:
    def __init__(
        self,
        records: dict[str, tuple[ir.Value, ir.Type]] = {},
        parent=None,
        name: str = "global",
    ) -> None:
        self.records = records
        self.parent = parent
        self.name = name
        pass

    def define(self, name: str, value: ir.Value, _t: ir.Type) -> ir.Value:
        assert self.records is not None
        self.records[name] = (value, _t)
        return value

    def lookup(self, name) -> tuple[ir.Value, ir.Type] | None:
        return self.__resolve(name)

    def __resolve(self, name: str) -> tuple[ir.Value, ir.Type] | None:
        assert self.records is not None
        if name in self.records:
            return self.records[name]
        elif self.parent:
            return self.parent.__resolve(name)
        else:
            return None
