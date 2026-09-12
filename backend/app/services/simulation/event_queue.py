"""
Deterministic Priority Event Queue for AI Governance Crisis Simulator.

Guarantees deterministic event ordering based on:
1. tick (ascending)
2. priority (ascending: lower number = higher urgency)
3. sequence_id (monotonic insertion counter)
4. event_id (lexicographic tie-breaker)
"""
import heapq
from typing import Any, List, Optional, Tuple

from app.schemas.simulation_models import SimulationEvent


class EventQueue:
    """
    Deterministic priority queue for simulation events.
    """

    def __init__(self):
        self._heap: List[Tuple[int, int, int, str, SimulationEvent]] = []
        self._sequence_counter: int = 0

    def schedule(self, event: SimulationEvent) -> None:
        """
        Schedules an event into the queue.
        """
        self._sequence_counter += 1
        entry = (event.tick, event.priority, self._sequence_counter, event.event_id, event)
        heapq.heappush(self._heap, entry)

    def schedule_batch(self, events: List[SimulationEvent]) -> None:
        """
        Schedules multiple events deterministically.
        """
        for event in events:
            self.schedule(event)

    def peek(self) -> Optional[SimulationEvent]:
        """
        Inspects the next scheduled event without removing it.
        """
        if not self._heap:
            return None
        return self._heap[0][4]

    def pop(self) -> Optional[SimulationEvent]:
        """
        Pops the highest priority ready event.
        """
        if not self._heap:
            return None
        return heapq.heappop(self._heap)[4]

    def pop_ready(self, current_tick: int) -> List[SimulationEvent]:
        """
        Extracts and returns all events scheduled for tick <= current_tick,
        strictly in deterministic priority order.
        """
        ready_events: List[SimulationEvent] = []
        while self._heap and self._heap[0][0] <= current_tick:
            ready_events.append(heapq.heappop(self._heap)[4])
        return ready_events

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def all_events(self) -> List[SimulationEvent]:
        """
        Returns a sorted list of all pending events currently in the queue.
        """
        sorted_entries = sorted(self._heap, key=lambda x: (x[0], x[1], x[2], x[3]))
        return [entry[4] for entry in sorted_entries]

    def clear(self) -> None:
        self._heap.clear()
        self._sequence_counter = 0
