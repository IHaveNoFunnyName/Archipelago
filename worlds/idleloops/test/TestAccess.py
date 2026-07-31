from . import IdleLoopsTestBase


class TestAllReachability(IdleLoopsTestBase):
    options = {"goal": 3}


class TestRestrictive(IdleLoopsTestBase):
    options = {"goal": 3, "logic_big_sphere1": 0, "logic_vanilla": 1, "logic_mana_reduction": 1, "logic_glasses": 1, "location_progress": 0}
