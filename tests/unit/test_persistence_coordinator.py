import time
import unittest
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from backend.simulation.persistence_coordinator import PersistenceCoordinator, TimerLike


class FakeTimer(TimerLike):
    def __init__(self, delay_seconds: float, callback: Callable[[], None]) -> None:
        self.delay_seconds = delay_seconds
        self.callback = callback
        self.started = False
        self.cancelled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        if not self.cancelled:
            self.callback()


class FakeTimerFactory:
    def __init__(self) -> None:
        self.timers: list[FakeTimer] = []

    def __call__(self, delay_seconds: float, callback: Callable[[], None]) -> FakeTimer:
        timer = FakeTimer(delay_seconds, callback)
        self.timers.append(timer)
        return timer


class PersistenceCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timer_factory = FakeTimerFactory()
        self.persist_calls: list[str] = []
        self.coordinator = PersistenceCoordinator(
            lambda: self.persist_calls.append("persist"),
            timer_factory=self.timer_factory,
        )

    def test_deferred_persist_waits_for_timer(self) -> None:
        self.coordinator.schedule_deferred_persist()

        self.assertEqual(self.persist_calls, [])
        self.assertTrue(self.timer_factory.timers[-1].started)

        self.timer_factory.timers[-1].fire()
        self.assertEqual(self.persist_calls, ["persist"])

    def test_rescheduling_cancels_previous_timer(self) -> None:
        self.coordinator.schedule_deferred_persist()
        first = self.timer_factory.timers[-1]
        self.coordinator.schedule_deferred_persist()
        second = self.timer_factory.timers[-1]

        self.assertTrue(first.cancelled)
        self.assertFalse(second.cancelled)

        first.fire()
        self.assertEqual(self.persist_calls, [])
        second.fire()
        self.assertEqual(self.persist_calls, ["persist"])

    def test_flush_immediately_cancels_pending_timer(self) -> None:
        self.coordinator.schedule_deferred_persist()
        timer = self.timer_factory.timers[-1]

        self.coordinator.flush_immediately()

        self.assertTrue(timer.cancelled)
        self.assertEqual(self.persist_calls, ["persist"])

        timer.fire()
        self.assertEqual(self.persist_calls, ["persist"])

    def test_stale_timer_tokens_do_not_persist(self) -> None:
        self.coordinator.schedule_deferred_persist()
        first = self.timer_factory.timers[-1]
        self.coordinator.schedule_deferred_persist()
        second = self.timer_factory.timers[-1]

        first.cancelled = False
        first.fire()
        self.assertEqual(self.persist_calls, [])

        second.fire()
        self.assertEqual(self.persist_calls, ["persist"])

    def test_shutdown_flushes_pending_state(self) -> None:
        self.coordinator.schedule_deferred_persist()

        self.coordinator.shutdown()

        self.assertEqual(self.persist_calls, ["persist"])

    def test_concurrent_flushes_serialize_persist_function(self) -> None:
        counter_lock = Lock()
        active = 0
        maximum_active = 0

        def persist() -> None:
            nonlocal active, maximum_active
            with counter_lock:
                active += 1
                maximum_active = max(maximum_active, active)
            time.sleep(0.02)
            with counter_lock:
                active -= 1

        coordinator = PersistenceCoordinator(persist, debounce_ms=0)
        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(lambda _: coordinator.flush_immediately(), range(8)))

        self.assertEqual(maximum_active, 1)


if __name__ == "__main__":
    unittest.main()
