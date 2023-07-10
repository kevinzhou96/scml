import random

import pytest
from negmas import ResponseType, SAOResponse

from scml.oneshot.agents import (
    GreedyOneShotAgent,
    GreedySingleAgreementAgent,
    GreedySyncAgent,
    RandomOneShotAgent,
)
from scml.oneshot.world import SCML2023OneShotWorld
from scml.scml2020.utils import (
    anac2023_oneshot_world_generator,
    anac_assigner_oneshot,
    anac_config_generator_oneshot,
)


def test_equal_exogenous_supply():
    world = SCML2023OneShotWorld(
        **SCML2023OneShotWorld.generate(
            agent_types=[
                GreedySyncAgent,
                GreedyOneShotAgent,
                GreedySingleAgreementAgent,
                RandomOneShotAgent,
            ],
            agent_processes=None,
            n_processes=2,
            n_steps=10,
            random_agent_types=False,
            production_costs=2,
            exogenous_price_dev=0.0,
            equal_exogenous_sales=True,
            equal_exogenous_supply=True,
        )
    )
    world.run()


def test_equal_exogenous_supply_stepping():
    world = SCML2023OneShotWorld(
        **SCML2023OneShotWorld.generate(
            agent_types=[
                GreedySyncAgent,
                GreedyOneShotAgent,
                GreedySingleAgreementAgent,
                RandomOneShotAgent,
            ],
            agent_processes=None,
            n_processes=2,
            n_steps=10,
            random_agent_types=False,
            production_costs=2,
            exogenous_price_dev=0.0,
            equal_exogenous_sales=True,
            equal_exogenous_supply=True,
            one_offer_per_step=True,
        )
    )
    while world.step():
        pass
    assert len(world.contracts_executed) > 0


def test_equal_exogenous_supply_stepping_with_no_action():
    world = SCML2023OneShotWorld(
        **SCML2023OneShotWorld.generate(
            agent_types=[
                GreedySyncAgent,
                GreedyOneShotAgent,
                GreedySingleAgreementAgent,
                RandomOneShotAgent,
            ],
            agent_processes=None,
            n_processes=2,
            n_steps=10,
            random_agent_types=False,
            production_costs=2,
            exogenous_price_dev=0.0,
            equal_exogenous_sales=True,
            equal_exogenous_supply=True,
            one_offer_per_step=True,
        )
    )
    world.step_with(actions=dict(), init=True)
    while world.step_with(actions=dict()):
        pass
    assert len(world.contracts_executed) > 0


def test_equal_exogenous_supply_stepping_with_random_action():
    world = SCML2023OneShotWorld(
        **SCML2023OneShotWorld.generate(
            agent_types=[
                GreedySyncAgent,
                GreedyOneShotAgent,
                GreedySingleAgreementAgent,
                RandomOneShotAgent,
            ],
            agent_processes=None,
            n_processes=2,
            n_steps=10,
            random_agent_types=False,
            production_costs=2,
            exogenous_price_dev=0.0,
            equal_exogenous_sales=True,
            equal_exogenous_supply=True,
            one_offer_per_step=True,
        )
    )
    agents = list(random.choices(list(world.agents.values()), k=1))
    world.step_with(actions=dict(), init=True)

    def make_actions():
        actions = dict()
        for agent in agents:
            negotiator, responses = None, dict()
            for t in ["buy", "sell"]:
                for partner, neg in agent.awi.current_negotiation_details[t].items():  # type: ignore
                    assert agent.id in (neg.buyer, neg.seller)
                    partner2 = neg.buyer if agent.id == neg.seller else neg.seller
                    assert partner2 == partner
                    negotiator = [
                        _.id
                        for _ in neg.nmi.mechanism.negotiators
                        if _.owner.id == agent.id
                    ][0]
                    partner = [
                        _.id
                        for _ in neg.nmi.mechanism.negotiators
                        if _.owner.id != agent.id
                    ][0]
                    responses[neg.nmi.mechanism.id] = {
                        negotiator: SAOResponse(
                            ResponseType.REJECT_OFFER, neg.nmi.random_outcome()
                        )
                    }

            actions[agent.id] = responses
        return actions

    actions = make_actions()
    while world.step_with(actions=actions):
        actions = make_actions()
    assert len(world.contracts_executed) > 0


@pytest.mark.parametrize("year", [2023])
def test_anac_single_world(year):
    configs = anac_config_generator_oneshot(
        year, n_competitors=1, n_agents_per_competitor=1
    )
    assigned = anac_assigner_oneshot(
        configs, 1, competitors=[RandomOneShotAgent], params=None, fair=False
    )
    assert len(assigned) == 1
    assigned = assigned[0][0]
    world = anac2023_oneshot_world_generator(year=year, **assigned)
    world.run()
    assert len(world.contracts_executed) > 0
