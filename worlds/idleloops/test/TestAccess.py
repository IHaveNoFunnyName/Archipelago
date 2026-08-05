from . import IdleLoopsTestBase


class TestAllReachability(IdleLoopsTestBase):
    options = {"goal": 3}


class TestRestrictive(IdleLoopsTestBase):
    options = {"goal": 3, "logic_vanilla": 1, "logic_mana_reduction": 1, "logic_glasses": 1}
