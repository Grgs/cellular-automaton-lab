import sys
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

try:
    from backend.rules import RuleRegistry
    from backend.rules.conway import ConwayLifeRule
    from backend.simulation.models import SimulationConfig, SimulationStateData
    from backend.simulation.runtime import RuntimeLoopService, SimulationRuntime, ThreadLike
    from backend.simulation.service import SimulationService
    from tests.unit.board_test_support import board_from_grid, regular_grid_from_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.rules import RuleRegistry
    from backend.rules.conway import ConwayLifeRule
    from backend.simulation.models import SimulationConfig, SimulationStateData
    from backend.simulation.runtime import RuntimeLoopService, SimulationRuntime, ThreadLike
    from backend.simulation.service import SimulationService
    from tests.unit.board_test_support import board_from_grid, regular_grid_from_board
from tests.unit.simulation_test_fixtures import BLINKER_PADDED_GRID


class FakeClock:
    def __init__(self) -> None:
        self.current = 0.0

    def monotonic(self) -> float:
        return self.current

    def sleep(self, delay: float) -> None:
        self.current += delay

    def advance(self, delay: float) -> None:
        self.current += delay


class FakeThread(ThreadLike):
    def __init__(
        self,
        *,
        target: Callable[[], None] | None = None,
        daemon: bool | None = None,
    ) -> None:
        self.target = target
        self.daemon = daemon
        self.started = False
        self.join_calls: list[float | None] = []
        self.alive = False

    def start(self) -> None:
        self.started = True
        self.alive = True

    def join(self, timeout: float | None = None) -> None:
        self.join_calls.append(timeout)
        self.alive = False

    def is_alive(self) -> bool:
        return self.alive


class TimedService(RuntimeLoopService):
    def __init__(self, clock: FakeClock, *, step_delay: float, target_delay: float) -> None:
        self._clock = clock
        self._step_delay = step_delay
        self._target_delay = target_delay
        self.steps = 0

    def runtime_plan(self) -> tuple[bool, float]:
        return True, self._target_delay

    def step_if_running(self) -> bool:
        self.steps += 1
        self._clock.advance(self._step_delay)
        return True


class SimulationRuntimeTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def create_runtime_with_fake_threads(self) -> tuple[SimulationRuntime, list[FakeThread]]:
        service = SimulationService(rule_registry=self.rule_registry)
        threads: list[FakeThread] = []

        def thread_factory(
            *,
            target: Callable[[], None] | None = None,
            daemon: bool | None = None,
        ) -> FakeThread:
            thread = FakeThread(target=target, daemon=daemon)
            threads.append(thread)
            return thread

        runtime = SimulationRuntime(
            service,
            sleep_fn=lambda _: None,
            thread_factory=thread_factory,
        )
        return runtime, threads

    def create_timed_service(
        self,
        clock: FakeClock,
        *,
        step_delay: float,
        target_delay: float,
    ) -> TimedService:
        return TimedService(clock, step_delay=step_delay, target_delay=target_delay)

    def test_run_once_steps_only_while_running(self) -> None:
        state = SimulationStateData(
            config=SimulationConfig.from_values(width=5, height=5, speed=6),
            running=False,
            generation=0,
            rule=ConwayLifeRule(),
            board=board_from_grid([row[:] for row in BLINKER_PADDED_GRID]),
        )
        service = SimulationService(rule_registry=self.rule_registry, state=state)
        runtime = SimulationRuntime(service)

        idle_delay = runtime.run_once()
        self.assertEqual(service.get_state().generation, 0)
        self.assertEqual(idle_delay, 0.2)

        service.start()
        active_delay = runtime.run_once()
        stepped = service.get_state()
        grid = regular_grid_from_board(stepped.board)
        assert grid is not None
        self.assertEqual(stepped.generation, 1)
        self.assertEqual(
            grid[:3],
            [
                [0, 0, 0, 0, 0],
                [1, 1, 1, 0, 0],
                [0, 0, 0, 0, 0],
            ],
        )
        self.assertGreater(active_delay, 0.0)
        self.assertLessEqual(active_delay, 1.0 / 6.0)

    def test_run_once_uses_updated_speed_for_delay(self) -> None:
        service = SimulationService(rule_registry=self.rule_registry)
        runtime = SimulationRuntime(service)

        service.update_config(speed=12)
        service.start()
        delay = runtime.run_once()

        self.assertGreater(delay, 0.0)
        self.assertLessEqual(delay, 1.0 / 12.0)
        self.assertEqual(service.get_state().generation, 1)

    def test_run_once_compensates_for_step_duration_when_calculating_sleep(self) -> None:
        clock = FakeClock()
        service = self.create_timed_service(clock, step_delay=0.02, target_delay=0.1)
        runtime = SimulationRuntime(service, sleep_fn=clock.sleep, monotonic_fn=clock.monotonic)

        delay = runtime.run_once()

        self.assertAlmostEqual(delay, 0.08)
        self.assertEqual(service.steps, 1)

    def test_repeated_run_once_hits_target_cycle_time_including_step_cost(self) -> None:
        clock = FakeClock()
        service = self.create_timed_service(clock, step_delay=0.02, target_delay=0.1)
        runtime = SimulationRuntime(service, sleep_fn=clock.sleep, monotonic_fn=clock.monotonic)

        for _ in range(5):
            delay = runtime.run_once()
            clock.sleep(delay)

        self.assertEqual(service.steps, 5)
        self.assertAlmostEqual(clock.current, 0.5)

    def test_run_once_never_returns_negative_sleep_when_step_exceeds_target_delay(self) -> None:
        clock = FakeClock()
        service = self.create_timed_service(clock, step_delay=0.12, target_delay=0.1)
        runtime = SimulationRuntime(service, sleep_fn=clock.sleep, monotonic_fn=clock.monotonic)

        delay = runtime.run_once()

        self.assertEqual(delay, 0.0)
        self.assertEqual(service.steps, 1)

    def test_runtime_stop_shuts_background_loop_down_cleanly(self) -> None:
        runtime, _ = self.create_runtime_with_fake_threads()
        runtime.start_background_loop()
        runtime.stop_background_loop()
        self.assertIsNone(runtime._thread)

    def test_start_background_loop_is_idempotent_while_thread_is_alive(self) -> None:
        runtime, threads = self.create_runtime_with_fake_threads()

        runtime.start_background_loop()
        runtime.start_background_loop()

        self.assertEqual(len(threads), 1)
        self.assertTrue(threads[0].started)
        self.assertTrue(threads[0].daemon)

    def test_start_background_loop_resets_stop_event_after_stop_and_restart(self) -> None:
        runtime, threads = self.create_runtime_with_fake_threads()

        runtime.start_background_loop()
        first_thread = threads[0]
        runtime.stop_background_loop()

        self.assertEqual(first_thread.join_calls, [1.0])
        self.assertTrue(runtime._stop_event.is_set())

        runtime.start_background_loop()

        self.assertEqual(len(threads), 2)
        self.assertIs(runtime._thread, threads[1])
        self.assertFalse(runtime._stop_event.is_set())
        self.assertTrue(threads[1].started)


if __name__ == "__main__":
    unittest.main()
