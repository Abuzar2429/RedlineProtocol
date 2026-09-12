"""
Virtual Event Clock for AI Governance Crisis Simulator.

Provides a deterministic virtual timeline without relying on wall-clock time:
T+00, T+01, T+02, ...
"""


class SimulationClock:
    """
    Virtual deterministic tick clock.
    """

    def __init__(self, initial_tick: int = 0):
        self._tick = initial_tick

    @property
    def current_tick(self) -> int:
        return self._tick

    @property
    def current_time(self) -> str:
        return self.format_time(self._tick)

    def advance(self, ticks: int = 1) -> int:
        """
        Advances the clock by the specified number of ticks (default 1).
        Returns the new current tick.
        """
        if ticks < 1:
            raise ValueError(f"Advance ticks must be positive, got {ticks}")
        self._tick += ticks
        return self._tick

    def set_tick(self, tick: int) -> None:
        """
        Sets the clock to a specific tick offset.
        """
        if tick < 0:
            raise ValueError(f"Tick cannot be negative, got {tick}")
        self._tick = tick

    def reset(self) -> None:
        """
        Resets the clock back to T+00.
        """
        self._tick = 0

    @staticmethod
    def format_time(tick: int) -> str:
        """
        Formats integer tick into standardized virtual timeline representation:
        e.g. 0 -> 'T+00', 5 -> 'T+05', 120 -> 'T+120'
        """
        return f"T+{tick:02d}"
