import numpy as np

from .pid import PID


def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


class LoadBalancer:
    def __init__(
        self,
        priority_groups: int,
        initial_kp: float = 0.3,
        initial_ki: float = 0.6,
        initial_kd: float = 0.1,
        learning_rate: float = 0.001,
        decay_rate: float = 0.99,
        event_threshold: float = 1e4,
        threshold_growth_rate: float = 1.1,
    ):
        self._group_event_counts = np.zeros(priority_groups)
        self._pid = PID(
            priority_groups,
            initial_kp,
            initial_ki,
            initial_kd,
            learning_rate,
            decay_rate,
        )
        self._group_event_counts_threshold = event_threshold
        self._threshold_growth_rate = threshold_growth_rate
        self._target_ratios = 1 / (np.arange(priority_groups) + 1)

    def register_event(self, priority_group: int):
        if not 0 <= priority_group < len(self._group_event_counts):
            raise ValueError(f"Invalid priority group: {priority_group}")

        self._group_event_counts[priority_group] += 1

        if self._group_event_counts.max() > self._group_event_counts_threshold:
            self._group_event_counts *= 0.5

        self._group_event_counts_threshold = max(
            self._group_event_counts_threshold * self._threshold_growth_rate, 1e4
        )

    def determine_priority_group(self, priority: int) -> int:
        total_group = self._group_event_counts.sum()

        if total_group == 0:
            return np.clip(priority - 1, 0, len(self._group_event_counts) - 1)

        processed_ratios = self._group_event_counts / total_group
        errors = self._target_ratios - processed_ratios

        control_outputs = self._pid.update(errors)

        return np.random.choice(
            np.arange(len(control_outputs)), p=softmax(control_outputs)
        )
