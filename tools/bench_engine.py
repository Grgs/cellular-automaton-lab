import statistics
import sys
import time
from pathlib import Path
from random import Random


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rules.conway import ConwayLifeRule
from backend.rules.archlife488 import ArchLife488Rule
from backend.rules.hexlife import HexLifeRule
from backend.rules.hexwhirlpool import HexWhirlpoolRule
from backend.rules.trilife import TriLifeRule
from backend.rules.whirlpool import WhirlpoolRule
from backend.simulation.engine import SimulationEngine
from backend.simulation.rule_context import build_rule_contexts_for_board
from backend.simulation.topology import ARCHIMEDEAN_488_GEOMETRY, SimulationBoard, empty_board


def reference_step_board(engine: SimulationEngine, board: SimulationBoard, rule) -> SimulationBoard:
    del engine
    topology = board.topology
    if topology.cell_count == 0:
        return board.clone()
    next_states = [rule.next_state(ctx) for ctx in build_rule_contexts_for_board(board)]
    return SimulationBoard(topology=topology, cell_states=next_states)


def build_board(geometry: str, width: int, height: int, max_state: int, seed: int) -> SimulationBoard:
    random = Random(seed)
    board = empty_board(geometry, width, height)
    if max_state == 1:
        board.cell_states = [1 if random.random() >= 0.5 else 0 for _ in range(board.topology.cell_count)]
    else:
        board.cell_states = [random.randint(0, max_state) for _ in range(board.topology.cell_count)]
    return board


def median_ms(runner, repeats: int = 7, warmups: int = 2) -> float:
    for _ in range(warmups):
        runner()
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        runner()
        timings.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(timings)


def benchmark_case(name: str, rule, board: SimulationBoard) -> dict[str, float]:
    optimized_engine = SimulationEngine()
    reference_engine = SimulationEngine()

    optimized_ms = median_ms(lambda: optimized_engine.step_board(board, rule))
    reference_ms = median_ms(lambda: reference_step_board(reference_engine, board, rule))
    speedup = reference_ms / optimized_ms if optimized_ms else float("inf")
    return {
        "optimized_ms": optimized_ms,
        "reference_ms": reference_ms,
        "speedup": speedup,
    }


def benchmark_board_case(name: str, rule, board: SimulationBoard) -> dict[str, float]:
    optimized_engine = SimulationEngine()
    reference_engine = SimulationEngine()

    optimized_ms = median_ms(lambda: optimized_engine.step_board(board, rule))
    reference_ms = median_ms(lambda: reference_step_board(reference_engine, board, rule))
    speedup = reference_ms / optimized_ms if optimized_ms else float("inf")
    return {
        "optimized_ms": optimized_ms,
        "reference_ms": reference_ms,
        "speedup": speedup,
    }


def main() -> None:
    board_cases = [
        ("square-conway", ConwayLifeRule(), build_board("square", 180, 120, 1, 101)),
        ("hex-hexlife", HexLifeRule(), build_board("hex", 180, 120, 1, 202)),
        ("triangle-trilife", TriLifeRule(), build_board("triangle", 180, 120, 1, 303)),
        ("square-whirlpool", WhirlpoolRule(), build_board("square", 150, 100, 4, 404)),
        ("hex-hexwhirlpool", HexWhirlpoolRule(), build_board("hex", 150, 100, 4, 505)),
        (
            "arch-archlife488",
            ArchLife488Rule(),
            build_board(ARCHIMEDEAN_488_GEOMETRY, 90, 60, 1, 606),
        ),
    ]

    print("Engine benchmark (median ms, lower is better)")
    print("Baseline = helper-driven reference step that approximates the pre-optimization path")
    print("")
    for name, rule, board in board_cases:
        result = benchmark_case(name, rule, board)
        print(
            f"{name:18s}  optimized={result['optimized_ms']:8.2f} ms  "
            f"reference={result['reference_ms']:8.2f} ms  speedup={result['speedup']:5.2f}x"
        )


if __name__ == "__main__":
    main()
