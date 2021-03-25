import random

import hypothesis.strategies as st
from hypothesis import given
from hypothesis import settings
from negmas import save_stats
from negmas.helpers import unique_name
from pytest import mark

import scml
from scml.oneshot import SCML2020OneShotWorld, builtin_agent_types
from scml.oneshot.agent import OneShotAgent
from scml.oneshot.agents import RandomOneShotAgent
from scml.oneshot.ufun import OneShotUFun
from scml.scml2020 import is_system_agent
from scml.scml2020.components import production

random.seed(0)

COMPACT = True
NOLOGS = True
# agent types to be tested
types = builtin_agent_types(False)
active_types = types
std_types = scml.scml2020.builtin_agent_types(as_str=False)
# try:
#     from scml_agents import get_agents
#
#     std_types += list(get_agents(2020, as_class=True, winners_only=True))
# except ImportError:
#     pass


def generate_world(
    agent_types,
    n_processes=3,
    n_steps=10,
    n_agents_per_process=2,
    n_lines=10,
    **kwargs,
):
    kwargs["no_logs"] = True
    kwargs["compact"] = True
    world = SCML2020OneShotWorld(
        **SCML2020OneShotWorld.generate(
            agent_types,
            n_processes=n_processes,
            n_steps=n_steps,
            n_lines=n_lines,
            n_agents_per_process=n_agents_per_process,
            **kwargs,
        )
    )
    for s1, s2 in zip(world.suppliers[:-1], world.suppliers[1:]):
        assert len(set(s1).intersection(set(s2))) == 0
    for s1, s2 in zip(world.consumers[:-1], world.consumers[1:]):
        assert len(set(s1).intersection(set(s2))) == 0
    for p in range(n_processes):
        assert len(world.suppliers[p + 1]) == n_agents_per_process
        assert len(world.consumers[p]) == n_agents_per_process
    for a in world.agents.keys():
        if is_system_agent(a):
            continue
        assert len(world.agent_inputs[a]) == 1
        assert len(world.agent_outputs[a]) == 1
        assert len(world.agent_processes[a]) == 1
        assert len(world.agent_suppliers[a]) == (
            n_agents_per_process if world.agent_inputs[a][0] != 0 else 1
        )
        assert len(world.agent_consumers[a]) == (
            n_agents_per_process if world.agent_outputs[a][0] != n_processes else 1
        )
    return world


@mark.parametrize("agent_type", types)
@given(n_processes=st.integers(2, 4))
@settings(deadline=300_000, max_examples=20)
def test_can_run_with_a_single_agent_type(agent_type, n_processes):
    world = generate_world(
        [agent_type],
        n_processes=n_processes,
        name=unique_name(
            f"scml2020tests/single/{agent_type.__name__}" f"Fine{n_processes}",
            add_time=True,
            rand_digits=4,
        ),
        compact=COMPACT,
        no_logs=NOLOGS,
    )
    world.run()
    save_stats(world, world.log_folder)


@given(
    agent_types=st.lists(
        st.sampled_from(active_types),
        min_size=1,
        max_size=len(active_types),
        unique=True,
    ),
    n_processes=st.integers(2, 4),
)
@settings(deadline=300_000, max_examples=20)
def test_can_run_with_a_multiple_agent_types(agent_types, n_processes):
    world = generate_world(
        agent_types,
        name=unique_name(
            f"scml2020tests/multi/{'-'.join(_.__name__[:3] for _ in agent_types)}/"
            f"Fine_p{n_processes}",
            add_time=True,
            rand_digits=4,
        ),
        n_processes=n_processes,
        compact=COMPACT,
        no_logs=NOLOGS,
    )
    world.run()
    save_stats(world, world.log_folder)


@given(n_processes=st.integers(2, 4))
@settings(deadline=300_000, max_examples=20)
def test_something_happens_with_random_agents(n_processes):
    world = generate_world(
        [RandomOneShotAgent],
        n_processes=n_processes,
        name=unique_name(
            f"scml2020tests/single/do_something/" f"Fine_p{n_processes}",
            add_time=True,
            rand_digits=4,
        ),
        compact=COMPACT,
        no_logs=NOLOGS,
        n_steps=15,
    )
    world.run()
    assert len(world.signed_contracts) + len(world.cancelled_contracts) != 0


def test_basic_awi_info_suppliers_consumers():
    world = SCML2020OneShotWorld(
        **SCML2020OneShotWorld.generate(
            agent_types=RandomOneShotAgent,
            n_steps=10,
            n_processes=2,
            compact=True,
            no_logs=True,
        )
    )
    for aid in world.agents:
        if is_system_agent(aid):
            continue
        a = world.agents[aid]
        assert a.id in a.awi.all_suppliers[a.awi.my_output_product]
        assert a.id in a.awi.all_consumers[a.awi.my_input_product]
        assert a.awi.my_consumers == world.agent_consumers[aid]
        assert a.awi.my_suppliers == world.agent_suppliers[aid]
        l = a.awi.my_input_product
        assert all(
            _.endswith(str(l - 1)) or a.awi.is_system(_) for _ in a.awi.my_suppliers
        )
        assert all(
            _.endswith(str(l + 1)) or a.awi.is_system(_) for _ in a.awi.my_consumers
        )


def test_generate():
    world = SCML2020OneShotWorld(
        **SCML2020OneShotWorld.generate(
            agent_types=RandomOneShotAgent,
            n_steps=10,
            n_processes=2,
            compact=True,
            no_logs=True,
        )
    )
    world.run()
    assert True


def test_a_tiny_world():
    world = generate_world(
        [RandomOneShotAgent],
        n_processes=2,
        n_steps=5,
        n_agents_per_process=2,
        n_lines=5,
    )
    world.run()
    assert True


def test_graph():
    world = generate_world(
        [RandomOneShotAgent],
        n_processes=2,
        n_steps=10,
        n_agents_per_process=2,
        n_lines=5,
    )
    world.graph(together=True)
    world.step()
    world.graph(steps=None, together=True)
    world.graph(steps=None, together=False)
    world.run()
    world.graph((0, world.n_steps), together=False)
    world.graph((0, world.n_steps), together=True)


def test_graphs_lead_to_no_unknown_nodes():
    world = SCML2020OneShotWorld(
        **SCML2020OneShotWorld.generate(agent_types=[RandomOneShotAgent], n_steps=10),
        construct_graphs=True,
    )
    world.graph((0, world.n_steps))


def test_ufun_min_max_in_world():
    for _ in range(20):
        world = SCML2020OneShotWorld(
            **SCML2020OneShotWorld.generate(
                agent_types=[RandomOneShotAgent], n_steps=10
            ),
            construct_graphs=False,
            compact=True,
            no_logs=True,
        )
        world.step()
        for aid, agent in world.agents.items():
            if is_system_agent(aid):
                continue
            ufun = agent.make_ufun(add_exogenous=True)
            ufun.find_limit(True)
            ufun.find_limit(False)
            mn, mx = ufun.min_utility, ufun.max_utility
            assert mx >= mn


@given(
    ex_qin=st.integers(0, 3),
    ex_qout=st.integers(0, 3),
    ex_pin=st.integers(2, 10),
    ex_pout=st.integers(2, 10),
    production_cost=st.integers(0, 2),
    storage_cost=st.floats(0.5, 1.5),
    delivery_penalty=st.floats(1.5, 2.5),
    level=st.integers(0, 2),
    force_exogenous=st.booleans(),
    lines=st.integers(1, 3),
    balance=st.integers(0, 100),
    input_penalty_scale=st.floats(0.1, 2),
    output_penalty_scale=st.floats(0.1, 4),
    inegs=st.integers(0, 3),
    onegs=st.integers(0, 3),
)
@settings(deadline=None)
def test_ufun_limits(
    ex_qin,
    ex_qout,
    ex_pin,
    ex_pout,
    production_cost,
    storage_cost,
    delivery_penalty,
    level,
    force_exogenous,
    lines,
    balance,
    input_penalty_scale,
    output_penalty_scale,
    inegs,
    onegs,
):
    # these cases do not happen in 2020. May be we still need to test them
    if inegs < 1 and onegs < 1:
        return
    if inegs > 0 and ex_qin > 0:
        return
    if onegs > 0 and ex_qout > 0:
        return
    _ufun_unit2(
        ex_qin,
        ex_qout,
        ex_pin,
        ex_pout,
        production_cost,
        storage_cost,
        delivery_penalty,
        level,
        force_exogenous,
        lines,
        balance,
        input_penalty_scale,
        output_penalty_scale,
        inegs,
        onegs,
    )


def _ufun_unit2(
    ex_qin,
    ex_qout,
    ex_pin,
    ex_pout,
    production_cost,
    storage_cost,
    delivery_penalty,
    level,
    force_exogenous,
    lines,
    balance,
    input_penalty_scale,
    output_penalty_scale,
    inegs,
    onegs,
):
    if level == 0:
        input_agent, output_agent = True, False
    elif level == 1:
        input_agent, output_agent = False, False
    else:
        input_agent, output_agent = False, True

    ufun = OneShotUFun(
        ex_qin=ex_qin,
        ex_qout=ex_qout,
        ex_pin=ex_pin,
        ex_pout=ex_pout,
        production_cost=production_cost,
        storage_cost=storage_cost,
        delivery_penalty=delivery_penalty,
        input_agent=input_agent,
        output_agent=output_agent,
        n_lines=lines,
        force_exogenous=force_exogenous,
        input_product=0 if input_agent else 2,
        input_qrange=(1, 15),
        input_prange=(1, 15),
        output_qrange=(1, 15),
        output_prange=(1, 15),
        n_input_negs=inegs,
        n_output_negs=onegs,
        current_step=0,
        input_penalty_scale=input_penalty_scale,
        output_penalty_scale=output_penalty_scale,
        current_balance=balance,
    )
    worst_gt, best_gt = ufun.find_limits_brute_force()
    mn, mx = worst_gt.utility, best_gt.utility
    assert mx >= mn, f"Worst: {worst_gt}\nBest : {best_gt}"
    if force_exogenous:
        best_optimal = ufun.find_limit_optimal(True)
        worst_optimal = ufun.find_limit_optimal(False)
        assert abs(mx - best_optimal.utility) < 1e-1, f"{best_gt}\n{best_optimal}"
        assert (mn - worst_optimal.utility) < 1e-1, f"{worst_gt}\n{worst_optimal}"
    #     best_greedy = ufun.find_limit_greedy(True)
    #     worst_greedy = ufun.find_limit_greedy(False)
    #     assert best_gt == best_greedy
    #     assert worst_gt == worst_greedy
    #     best = ufun.find_limit(True)
    #     worst = ufun.find_limit(False)
    #     assert best_gt == best
    #     assert worst_gt == worst


def test_ufun_limits_example():
    _ufun_unit2(
        ex_qin=1,
        ex_qout=0,
        ex_pin=2,
        ex_pout=2,
        production_cost=0,
        storage_cost=0.5,
        delivery_penalty=1.5,
        level=0,
        force_exogenous=True,
        lines=1,
        balance=1,
        input_penalty_scale=0.1,
        output_penalty_scale=0.1,
        inegs=1,
        onegs=1,
    )


@given(
    ex_qin=st.integers(0, 10),
    ex_qout=st.integers(0, 10),
    ex_pin=st.integers(2, 10),
    ex_pout=st.integers(2, 10),
    production_cost=st.integers(1, 5),
    storage_cost=st.floats(0.5, 1.5),
    delivery_penalty=st.floats(1.5, 2.5),
    level=st.integers(0, 2),
    force_exogenous=st.booleans(),
    qin=st.integers(0, 10),
    qout=st.integers(0, 10),
    pin=st.integers(2, 10),
    pout=st.integers(2, 10),
    lines=st.integers(1, 15),
    balance=st.integers(0, 1000),
)
@settings(deadline=None)
def test_ufun_unit(
    ex_qin,
    ex_qout,
    ex_pin,
    ex_pout,
    production_cost,
    storage_cost,
    delivery_penalty,
    level,
    force_exogenous,
    qin,
    qout,
    pin,
    pout,
    lines,
    balance,
):
    _ufun_unit(
        ex_qin,
        ex_qout,
        ex_pin,
        ex_pout,
        production_cost,
        storage_cost,
        delivery_penalty,
        level,
        force_exogenous,
        qin,
        qout,
        pin,
        pout,
        lines,
        balance,
    )


def _ufun_unit(
    ex_qin,
    ex_qout,
    ex_pin,
    ex_pout,
    production_cost,
    storage_cost,
    delivery_penalty,
    level,
    force_exogenous,
    qin,
    qout,
    pin,
    pout,
    lines,
    balance,
):
    if level == 0:
        input_agent, output_agent = True, False
    elif level == 1:
        input_agent, output_agent = False, False
    else:
        input_agent, output_agent = False, True

    ufun = OneShotUFun(
        ex_qin=ex_qin,
        ex_qout=ex_qout,
        ex_pin=ex_pin,
        ex_pout=ex_pout,
        production_cost=production_cost,
        storage_cost=storage_cost,
        delivery_penalty=delivery_penalty,
        input_agent=input_agent,
        output_agent=output_agent,
        n_lines=lines,
        force_exogenous=force_exogenous,
        input_product=0 if input_agent else 2,
        input_qrange=(1, 15),
        input_prange=(1, 15),
        output_qrange=(1, 15),
        output_prange=(1, 15),
        n_input_negs=5,
        n_output_negs=5,
        current_step=0,
        input_penalty_scale=1,
        output_penalty_scale=3,
        current_balance=balance,
    )
    # if force_exogenous:
    # for v in (True, False):
    # a = ufun.find_limit_greedy(v)
    # try:
    #     b = ufun.find_limit_optimal(v, check=True)
    # except:
    #     pass
    # else:
    #     # assert a == b, f"Failed for {v} Greedy gave {a}\nOptimal gave {b}"
    #     assert (v and b >= a) or (
    #         not v and b <= a
    #     ), f"Failed for {v} Greedy gave {a}\nOptimal gave {b}"
    ufun.best = ufun.find_limit(True)
    ufun.worst = ufun.find_limit(False)

    mn, mx = ufun.min_utility, ufun.max_utility
    if mx is None:
        mx = float("inf")
    if mn is None:
        mn = float("-inf")

    assert mx >= mn or mx == mn == 0
    u = ufun.from_offers(
        [(qin, 0, pin / qin if qin else 0), (qout, 0, pout / qout if qout else 0)],
        [False, True],
    )
    # u = ufun.from_aggregates(qin, qout, pin, pout)
    # assert mn <= u <= mx, f"{mn}, {u}, {mx}\nworst: {ufun.worst}\nbest: {ufun.best}"


def test_ufun_unit_example():
    _ufun_unit(
        ex_qin=0,
        ex_qout=1,
        ex_pin=2,
        ex_pout=2,
        production_cost=1,
        storage_cost=0.5,
        delivery_penalty=1.5,
        level=0,
        force_exogenous=True,
        qin=0,
        qout=0,
        pin=2,
        pout=2,
        lines=10,
        balance=float("inf"),
    )


def test_ufun_example():
    _ufun_unit(
        ex_qin=0,
        ex_qout=0,
        ex_pin=0,
        ex_pout=0,
        production_cost=1,
        storage_cost=0.5,
        delivery_penalty=1.5,
        level=0,
        force_exogenous=False,
        qin=1,
        qout=1,
        pin=2,
        pout=4,
        lines=10,
        balance=float("inf"),
    )


def test_builtin_agent_types():
    from negmas.helpers import get_full_type_name

    strs = scml.oneshot.builtin_agent_types(True)
    types = scml.oneshot.builtin_agent_types(False)
    assert len(strs) == len(types)
    assert len(strs) > 0
    assert all(
        [
            get_full_type_name(a).split(".")[-1] == b.split(".")[-1]
            for a, b in zip(types, strs)
        ]
    )


@given(
    atype=st.lists(
        st.sampled_from(std_types + types), unique=True, min_size=2, max_size=6
    )
)
@settings(deadline=900_000, max_examples=10)
def test_adapter(atype):
    world = SCML2020OneShotWorld(
        **SCML2020OneShotWorld.generate(agent_types=atype, n_steps=10),
        construct_graphs=False,
        compact=True,
        no_logs=True,
    )
    world.run()
