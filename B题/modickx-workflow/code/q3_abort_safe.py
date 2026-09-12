"""GREEDY variant: never walk SAFE/centerline; abandon leftovers instead.

Original GREEDY is unchanged. This strategy keeps the seven-point tour,
certified clears, and greedy localize, then drops any remaining detected
channel that would otherwise enter the SAFE corridor.
"""
from q3_runner import Q3Runner


class GreedyAbortRunner(Q3Runner):
    def __init__(self, robot):
        super().__init__(robot, "GREEDY")
        self.abandoned = []

    def _abandon(self, k: int, reason: str) -> None:
        ch = self.state.channels[k]
        if ch.status == "cleared":
            return
        if k not in self.abandoned:
            self.abandoned.append(k)
            self._note(op="abort_safe", k=k, reason=reason, virtual_time=self.state.virtual_time)
        if k in self.state.P:
            self.state.P.remove(k)

    def safe_channel(self, k: int) -> None:
        self._abandon(k, "safe")

    def centerline_clear(self, k: int) -> None:
        self._abandon(k, "centerline")

    def run(self) -> dict:
        result = super().run()
        uncleared = [
            k for k, ch in self.state.channels.items()
            if ch.ever_detected and ch.status != "cleared"
        ]
        result.update(
            strategy="GREEDY_ABORT",
            abandoned_channels=list(self.abandoned),
            uncleared_detected_channels=uncleared,
            experimental_incomplete_allowed=True,
        )
        return result
