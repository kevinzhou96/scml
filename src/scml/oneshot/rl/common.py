from abc import ABC, abstractmethod
from typing import Any, Callable, Union

import numpy as np
from negmas import Agent, AgentWorldInterface, World

__all__ = ["isin", "WorldFactory", "RLState", "RLAction", "RLModel", "model_wrapper"]


def isin(x: int | tuple[int, int], y: tuple[int, int] | int):
    """Checks that x is within the range specified by y. Ugly but works"""
    if isinstance(x, tuple):
        if isinstance(y, tuple):
            return y[0] <= x[0] <= y[-1]
        return x[0] == y == x[-1]
    if isinstance(y, tuple):
        return y[0] <= x <= y[-1]
    return x == y


class WorldFactory(ABC):
    """Generates worlds satisfying predefined conditions and tests for them"""

    def __call__(self) -> tuple[World, Agent]:
        """Generates a world with one agent to be controlled externally and returns both"""
        ...

    @abstractmethod
    def is_valid_world(self, world: World) -> bool:
        """Checks that the given world could have been generated from this generator"""
        ...

    @abstractmethod
    def is_valid_awi(self, awi: AgentWorldInterface) -> bool:
        """Checks that the given AWI is connected to a world that could have been generated from this generator"""
        ...

    @abstractmethod
    def contains_factory(self, generator: "WorldFactory") -> bool:
        """Checks that the any world generated from the given `generator` could have been generated from this generator"""
        ...

    def __contains__(
        self, other: "Union[World, AgentWorldInterface, WorldFactory]"
    ) -> bool:
        if isinstance(other, WorldFactory):
            return self.contains_factory(other)
        if isinstance(other, AgentWorldInterface):
            return self.is_valid_awi(other)
        return self.is_valid_world(other)


RLState = np.ndarray
"""We assume that RL states are numpy arrays"""
RLAction = np.ndarray
"""We assume that RL actions are numpy arrays"""
RLModel = Callable[[RLState], RLAction]
"""A policy is a callable that receives a state and returns an action"""


def model_wrapper(model, deterministic: bool = False) -> RLModel:
    """Wraps a stable_baselines3 model as an RL model"""

    return lambda obs: model.predict(obs, deterministic=deterministic)[0]
