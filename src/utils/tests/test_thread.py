from time import sleep

from utils.thread import BackgroundRepeater


class RepeaterTest(BackgroundRepeater):

    def __init__(self, iterations: int):
        self.iterations = iterations
        self.iteration_count = 0
        super().__init__(sleep_interval=0.1)

    def _do_run(self) -> bool:
        self.iteration_count += 1
        return self.iteration_count > self.iterations


def test_kill_repeater():
    r = RepeaterTest(iterations=1000000000)
    r.start()
    sleep(1)
    r.kill()
    r.join(10)

    assert r.iteration_count < r.iterations


def test_repeater_stops_after_hitting_iteration_limit():
    r = RepeaterTest(iterations=2)
    r.start()
    r.join(2)

    assert r.iteration_count == r.iterations + 1
