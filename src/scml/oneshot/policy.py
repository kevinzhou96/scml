from abc import ABC, abstractmethod
from typing import Any

from negmas.gb.common import ResponseType
from negmas.helpers.strings import itertools
from negmas.outcomes import Outcome
from negmas.sao.common import SAOResponse, SAOState

from .agent import OneShotSyncAgent

__all__ = ["OneShotPolicy"]


class OneShotPolicy(OneShotSyncAgent, ABC):
    def encode_state(self, mechanism_states: dict[str, SAOState]) -> Any:
        """
        Called to generate a state to be passed to the act() method. The default is all of `awi.state` of type `OneShotState`
        """
        return self.awi.default_encoded_state(mechanism_states)

    @abstractmethod
    def act(self, state: Any) -> Any:
        """
        The main policy. Generates an action given a state
        """
        offers = dict()
        for supplier in state.my_suppliers:
            offers[supplier] = SAOResponse(
                ResponseType.REJECT_OFFER,
                self.awi.current_input_outcome_space.random_outcome(),
            )
        for consumer in state.my_consumers:
            offers[consumer] = SAOResponse(
                ResponseType.REJECT_OFFER,
                self.awi.current_output_outcome_space.random_outcome(),
            )
        return offers

    def decode_action(self, action: Any) -> dict[str, SAOResponse]:
        """
        Generates offers to all partners from an encoded action. Default is to return the action as it is assuming it is a `dict[str, SAOResponse]`
        """
        assert (
            isinstance(action, dict)
            and all(isinstance(_, str) for _ in action.keys())
            and all(isinstance(_, SAOResponse) for _ in action.values())
        )
        return action

    def counter_all(
        self, offers: dict[str, Outcome], states: dict[str, SAOState]
    ) -> dict[str, SAOResponse]:
        """Calculate a response to all offers from all negotiators
        (negotiator ID is the key).

        Args:
            offers: Maps negotiator IDs to offers
            states: Maps negotiator IDs to offers AT the time the offers were made.

        Returns:
            A dictionary mapping negotiator ID to an `SAOResponse`. The response
            per agent consist of a tuple. In case of acceptance or ending the
            negotiation the second item of the tuple should be None. In case of
            rejection, the second item should be the counter offer.


        Remarks:
            - The response type CANNOT be WAIT.
            - If the system determines that a loop is formed, the agent may
            receive this call for a subset of negotiations not all of them.

        """
        return self.decode_action(self.act(self.encode_state(states)))

    def first_proposals(self) -> dict[str, Outcome]:
        """
        Gets a set of proposals to use for initializing the negotiation.

        Returns:
            A dictionary mapping each negotiator (in self.negotiators dict) to
            an outcome to be used as the first proposal if the agent is to start
            a negotiation.

        """
        partners = [_ for _ in self.awi.my_suppliers if not self.awi.is_system(_)]
        partners += [_ for _ in self.awi.my_consumers if not self.awi.is_system(_)]

        def _state():
            return SAOState(started=True, n_negotiators=2)

        return self.counter_all(
            offers=dict(zip(partners, itertools.repeat(None))),
            states=dict(zip(partners, itertools.repeat(_state()))),
        )
