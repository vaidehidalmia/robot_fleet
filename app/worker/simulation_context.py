from typing import Callable

class SimulationContext:
    def __init__(
        self,
        cancel_simulation_task: Callable[[], None],
        update_simulation_status: Callable[[str], None],
    ):
        self.cancel_simulation_task = cancel_simulation_task
        self.update_simulation_status = update_simulation_status