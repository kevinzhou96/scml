import itertools
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict

from negmas import (
    Breach,
    Contract,
    MechanismState,
    Negotiator,
    NegotiatorMechanismInterface,
    RenegotiationRequest,
    UtilityFunction,
    Value,
)
from negmas.events import Notification
from negmas.helpers import get_class
from negmas.outcomes import Issue, Outcome

from scml.scml2019.agent import SCML2019Agent
from scml.scml2019.awi import SCMLAWI
from scml.scml2019.common import (
    CFP,
    DEFAULT_NEGOTIATOR,
    Factory,
    FinancialReport,
    Loan,
    ProductionFailure,
    ProductionReport,
    SCMLAgreement,
)
from scml.scml2019.consumers import ConsumptionProfile, JustInTimeConsumer
from scml.scml2019.schedulers import GreedyScheduler, ScheduleInfo, Scheduler
from scml.scml2019.simulators import (
    FactorySimulator,
    FastFactorySimulator,
    storage_as_array,
    temporary_transaction,
)

if True:
    from typing import (
        Any,
        Callable,
        Collection,
        Dict,
        Iterable,
        List,
        Optional,
        Type,
        Union,
    )

__all__ = [
    "FactoryManager",
    "DoNothingFactoryManager",
    "GreedyFactoryManager",
]


class FactoryManager(SCML2019Agent, ABC):
    """Base factory manager class that will be inherited by participant negmas in ANAC 2019.

    The agent can access the world simulation in one of two ways:

    1. Attributes and methods available in the Agent-SCML2020World-Interface (See `SCMLAWI` documentation for those).
    2. Attributes and methods in the `FactoryManager` object itself. All factory managers will have the following
       attributes and methods that simplify the interaction with the world simulation. Some of these attributes/methods
       are convenient ways to access functionality already available in the agent's internal `SCMLAWI`.

    **Attributes**

    *Agent information*

    - `id` : The unique ID assigned to this agent. This is unique system-wide and is what is used in contracts, CFPs,
      etc.
    - `name`: A name of the agent used for display purposes only. The simulator never accesses or uses this name except
      in printing and logging.
    - `uuid` : Another name of the `id` .
    - `type_name` : A string giving the type of the agent (as a fully qualified python class name).

    *Capabilities/Profiles*

    - `line_profiles` : A mapping specifying for each line index, all the profiles that can be run on it
    - `process_profiles` : A mapping specifying for each `Process` index, all the profiles used to run it in the factory
    - `producing` : Mapping from a product index to all manufacturing processes that can generate it
    - `consuming` : Mapping from a product index to all manufacturing processes that can consume it
    - `compiled_profiles` : All the profiles to be used by the factory belonging to this agent compiled to use process
      indices
    - `max_storage` : Maximum storage available to the agent. Zero, None or float('inf') all indicate unlimited storage.

    *Production Graph* (also accessible through *awi*)

    - `products` : List of products in the system
    - `processes` : List of processes in the system

    *Helper Objects*

    - `awi` : The `SCMLAWI` instance assigned to this agent. It can be used to interact with the simulation (See
      `SCMLAWI` documentation).
    - `simulator` : A `FactorySimulator` object that can be used to simulate what happens in the `Factory` assigned to
      this agent when given operations are conducted (e.g. production, paying money, etc).

    *Negotiations/Contracts*

    - `requested_negotiations` : A dynamic list of negotiations currently requested by the agent but not started.
      *Correct management of this list is only possible if the agent **always** uses `request_negotiation` method of
      this class (see methods later) rather than directly calling request_method on the `SCMLAWI` ( `awi` ) member.
    - `running_negotiations` : A dynamic list of negotiations currently running involving this agent.
      *Correct management of this list is only possible if the agent **always** uses `request_negotiation` method of
      this class (see methods later) rather than directly calling request_method on the `SCMLAWI` ( `awi` ) member.
    - `unsigned_contracts` : A dynamic list of negotiations contracts concluded involving this agent but not yet signed.
      *Correct management of this list is only possible if the agent **always** uses `request_negotiation` method of
      this class (see methods later) rather than directly calling request_method on the `SCMLAWI` ( `awi` ) member.

    *Simulation attributes* (also accessible through *awi*)

    - `transportation_delay` : The transportation delay in the system.
    - `current_step` : Current simulation step.
    - `immediate_negotiations` : Whether or not negotiations start immediately upon registration (default is to start on
      the next production step)
    - `negotiation_speed_multiple` : The number of negotiation rounds (steps) conducted in a single production step
    - `transportation_delay` : Transportation delay in the system. Default is zero


    **Methods** (Callable by the agent)

    *Actions on the world*

    - `request_negotiation` : Called to request a negotiation based on a `CFP` .

    *Scheduling and simulation helpers*

    - `can_expect_agreement` : Checks if it is possible in principle to get an agreement on this CFP by the time it
      becomes executable.


    **Callbacks** (Callable by the simulation)

    *Decision callbacks* (Called to make decisions)

        - Negotiation and Contracts

            - `respond_to_negotiation_request` : Decide whether or not to engage in a negotiation on a `CFP` that was
              published earlier by this factory manager. If accepted, the agent should return a `SAONegotiator` object.
            - `sign_contract` : Decide whether or not to sign the contract. If accepted, the agent should return its own ID.
            - `confirm_contract_execution` : Decide whether or not to go on with executing a contract that the agent already
              signed. If rejected (by returning `False` ), a refusal-to-execute breach will be recorded.

        - Breach related

            - `confirm_partial_execution` : Decide whether the agent agrees to partial execution. Called only when the
              the partner of this agent commits a partial breach (of level < 1) and this agent commits no breaches.
            - `set_renegotiation_agenda` : Decide what are the issues and ranges of acceptable values to re-negotiate about.
              Called only in case of breaches.
            - `respond_to_renegotiation_request` : Decide whether or not to engage in a re-negotiation.

        - Financial

            - `confirm_loan` : Decide whether or not to accept an offered loan. *In ANAC 2019 league, loans are not allowed
              and this callback will never be called by the simulator.

    *Time-dependent callbacks* (Information callback called at predefined times)

        - `init` : Called once before any production or negotiations to initiate the agent.
        - `step` : Called at every production step.

    *Information callbacks* (Called to inform the agent about events)

        - CFP related

            - `on_new_cfp` : Called whenever a `CFP` on a `Product` for which the agent has already registered interest
              (using `register_interest` method of its `awi`) is published. By default all agents register interest in the
              products they can consume or produce according to their profiles.
            - `on_remove_cfp` : Called whenever a `CFP` on a `Product` for which the agent has already registered interest
              (using `register_interest` method of its `awi`) is removed from the bulletin-board.

        - Negotiation related

            - `on_neg_request_accepted` : Called when a negotiation request of the agent is accepted
            - `on_neg_request_rejected` : Called when a negotiation request of the agent is rejected
            - `on_negotiation_success` : Called when a negotiation of which the agent is a party succeeds with an agreement.
            - `on_negotiation_failure` : Called when a negotiation of which the agent is a party ends without agreement.

        - Contract related

            - `on_contract_cancelled` : Called whenever a `Contract` of which the agent is a party is cancelled because the
              other party refused to sign it.
            - `on_contract_signed` : Called whenever a `Contract` of which the agent is a party is signed by both patners.
            - `on_contract_nullified` : Called whenever a `Contract` of which the agent is a party is nullified by the
              simulator as a part of bankruptcy processing.
            - `on_contract_executed` : Called when a contract executes completely and successfully.
            - `on_contract_breached` : Called when a contract is breached after complete contract processing.

        - Production and factory related

            - `on_production_failure` : Called whenever a scheduled production (see `SCMLAWI` for production commands)
              fails
            - `on_inventory_change` : Called whenever there is a change in the inventory (something is moved in or out
              or out of storage due to an event other than production (e.g. contract execution).
            - `on_cash_transfer` : Called whenever cash is transferred to or from the factory's wallet.

        - About other agents

            - `on_agent_bankrupt` : Called whenever another agent goes bankrupt
            - `on_new_report` : Called whenever a new report of another agent for which this agent has registered interest
              is published. Interest is registered using the agent's `awi` 's `receive_financial_reports` method.

    """

    def __init__(
        self,
        name=None,
        simulator_type: Union[str, Type[FactorySimulator]] = FastFactorySimulator,
    ):
        super().__init__(name=name)
        self.transportation_delay = 0
        """Transportation delay in the world"""
        self.simulator: Optional[FactorySimulator] = None
        """The simulator used by this agent"""
        self.simulator_type: Type[FactorySimulator] = get_class(
            simulator_type, scope=globals()
        )
        """Simulator type (as a class)"""
        self.current_step = 0
        """Current simulation step"""
        self.max_storage: int = 0
        """Maximum storage available to the agent"""

    def init_(self):
        state: Factory = self.awi.state
        self.current_step = state.next_step
        self.max_storage = state.max_storage
        self.simulator = self.simulator_type(
            initial_wallet=state.wallet,
            initial_storage=state.storage,
            n_steps=self.awi.n_steps,
            n_products=len(self.awi.products),
            profiles=state.profiles,
            max_storage=self.max_storage,
        )
        super().init_()

    def step_(self):
        state = self.awi.state
        self.simulator.set_state(
            self.current_step,
            wallet=state.wallet,
            loans=state.loans,
            storage=storage_as_array(state.storage, n_products=len(self.products)),
            line_schedules=state.line_schedules,
        )
        self.current_step += 1
        self.step()

    @abstractmethod
    def on_production_failure(self, failures: List[ProductionFailure]) -> None:
        """Called with a list of `ProductionFailure` records on production failure."""

    @abstractmethod
    def on_production_success(self, reports: List[ProductionReport]) -> None:
        """Called with a list of `ProductionReport` records on production success"""


class DoNothingFactoryManager(FactoryManager):
    """The default factory manager that will be implemented by the committee of ANAC-SCML 2019"""

    def init(self):
        pass

    def step(self):
        pass

    def on_neg_request_rejected(self, req_id: str, by: Optional[List[str]]):
        pass

    def on_neg_request_accepted(
        self, req_id: str, mechanism: NegotiatorMechanismInterface
    ):
        pass

    def on_negotiation_failure(
        self,
        partners: List[str],
        annotation: Dict[str, Any],
        mechanism: NegotiatorMechanismInterface,
        state: MechanismState,
    ) -> None:
        pass

    def on_negotiation_success(
        self, contract: Contract, mechanism: NegotiatorMechanismInterface
    ) -> None:
        pass

    def on_contract_signed(self, contract: Contract) -> None:
        pass

    def on_contract_cancelled(self, contract: Contract, rejectors: List[str]) -> None:
        pass

    def on_contract_executed(self, contract: Contract) -> None:
        pass

    def on_contract_breached(
        self, contract: Contract, breaches: List[Breach], resolution: Optional[Contract]
    ) -> None:
        pass

    def sign_contract(self, contract: Contract) -> Optional[str]:
        return self.id

    def on_contract_nullified(
        self, contract: Contract, bankrupt_partner: str, compensation: float
    ) -> None:
        pass

    def on_agent_bankrupt(self, agent_id: str) -> None:
        pass

    def confirm_partial_execution(
        self, contract: Contract, breaches: List[Breach]
    ) -> bool:
        return True

    def on_remove_cfp(self, cfp: "CFP") -> None:
        pass

    def on_production_failure(self, failures: List[ProductionFailure]) -> None:
        pass

    def respond_to_negotiation_request(
        self, cfp: "CFP", partner: str
    ) -> Optional[Negotiator]:
        return None

    def confirm_contract_execution(self, contract: Contract) -> bool:
        return True

    def set_renegotiation_agenda(
        self, contract: Contract, breaches: List[Breach]
    ) -> Optional[RenegotiationRequest]:
        return None

    def respond_to_renegotiation_request(
        self, contract: Contract, breaches: List[Breach], agenda: RenegotiationRequest
    ) -> Optional[Negotiator]:
        return None

    def confirm_loan(self, loan: Loan, bankrupt_if_rejected: bool) -> bool:
        """called by the world manager to confirm a loan if needed by the buyer of a contract that is about to be
        breached"""
        return bankrupt_if_rejected

    def on_new_cfp(self, cfp: "CFP") -> None:
        pass

    def on_inventory_change(self, product: int, quantity: int, cause: str) -> None:
        pass

    def on_production_success(self, reports: List[ProductionReport]) -> None:
        pass

    def on_cash_transfer(self, amount: float, cause: str) -> None:
        pass

    def on_new_report(self, report: FinancialReport):
        pass


class GreedyFactoryManager(DoNothingFactoryManager):
    """The default factory manager that will be implemented by the committee of ANAC-SCML 2019"""

    def on_production_failure(self, failures: List[ProductionFailure]) -> None:
        pass

    def on_production_success(self, reports: List[ProductionReport]) -> None:
        pass

    def confirm_loan(self, loan: Loan, bankrupt_if_rejected: bool) -> bool:
        return bankrupt_if_rejected

    def confirm_contract_execution(self, contract: Contract) -> bool:
        return True

    def set_renegotiation_agenda(
        self, contract: Contract, breaches: List[Breach]
    ) -> Optional[RenegotiationRequest]:
        return None

    def respond_to_renegotiation_request(
        self, contract: Contract, breaches: List[Breach], agenda: RenegotiationRequest
    ) -> Optional[Negotiator]:
        return None

    def __init__(
        self,
        name=None,
        simulator_type: Union[str, Type[FactorySimulator]] = FastFactorySimulator,
        scheduler_type: Union[str, Type[Scheduler]] = GreedyScheduler,
        scheduler_params: Optional[Dict[str, Any]] = None,
        optimism: float = 0.0,
        negotiator_type: Union[str, Type[Negotiator]] = DEFAULT_NEGOTIATOR,
        negotiator_params: Optional[Dict[str, Any]] = None,
        n_retrials=5,
        use_consumer=True,
        reactive=True,
        sign_only_guaranteed_contracts=False,
        riskiness=0.0,
        max_insurance_premium: float = 0.1,
        reserved_value: float = -float("inf"),
    ):
        super().__init__(name=name, simulator_type=simulator_type)
        self.negotiator_type = get_class(negotiator_type, scope=globals())
        self.negotiator_params = (
            negotiator_params if negotiator_params is not None else {}
        )
        self.optimism = optimism
        self.ufun_factory: Union[
            Type[NegotiatorUtility], Callable[[Any, Any], NegotiatorUtility]
        ]
        if optimism < 1e-6:
            self.ufun_factory = PessimisticNegotiatorUtility
        elif optimism > 1 - 1e-6:
            self.ufun_factory = OptimisticNegotiatorUtility
        else:
            self.ufun_factory: NegotiatorUtility = (
                lambda agent, annotation: AveragingNegotiatorUtility(
                    agent=agent, annotation=annotation, optimism=self.optimism
                )
            )
        if max_insurance_premium < 0.0:
            warnings.warn(
                f"Negative max insurance ({max_insurance_premium}) is deprecated. Set max_insurance_premium = inf "
                f"for always buying and max_insurance_premium = 0.0 for never buying. Will continue assuming inf"
            )
            max_insurance_premium = float("inf")
        self.__reserved_value = reserved_value
        self.max_insurance_premium = max_insurance_premium
        self.n_retrials = n_retrials
        self.n_neg_trials: Dict[str, int] = defaultdict(int)
        self.consumer = None
        self.use_consumer = use_consumer
        self.reactive = reactive
        self.sign_only_guaranteed_contracts = sign_only_guaranteed_contracts
        self.contract_schedules: Dict[str, ScheduleInfo] = {}
        self.riskiness = riskiness
        self.negotiation_margin = int(round(n_retrials * max(0.0, 1.0 - riskiness)))
        self.scheduler_type: Type[Scheduler] = get_class(
            scheduler_type, scope=globals()
        )
        self.scheduler: Scheduler = None
        self.scheduler_params: Dict[str, Any] = (
            scheduler_params if scheduler_params is not None else {}
        )

    def total_utility(self, contracts: Collection[Contract] = ()) -> float:
        """Calculates the total utility for the agent of a collection of contracts"""
        if self.scheduler is None:
            raise ValueError("Cannot calculate total utility without a scheduler")
        min_concluded_at = self.awi.current_step
        min_sign_at = min_concluded_at + self.awi.default_signing_delay
        with temporary_transaction(self.scheduler):
            schedule = self.scheduler.schedule(
                contracts=contracts,
                assume_no_further_negotiations=False,
                ensure_storage_for=self.transportation_delay,
                start_at=min_sign_at,
            )
        if not schedule.valid:
            return float("-inf")
        return schedule.final_balance

    def init(self):
        self.negotiation_margin = max(
            self.negotiation_margin,
            int(round(len(self.products) * max(0.0, 1.0 - self.riskiness))),
        )
        if self.use_consumer:
            # @todo add the parameters of the consumption profile as parameters of the greedy factory manager
            profiles = dict(
                zip(
                    self.consuming.keys(),
                    (
                        ConsumptionProfile(schedule=[_] * self.awi.n_steps)
                        for _ in itertools.repeat(0)
                    ),
                )
            )
            self.consumer: JustInTimeConsumer = JustInTimeConsumer(
                profiles=profiles,
                consumption_horizon=self.awi.n_steps,
                immediate_cfp_update=True,
                name=self.name,
            )
            self.consumer.id = self.id
            self.consumer.awi = self.awi
            self.consumer.init_()
        self.scheduler = self.scheduler_type(
            manager_id=self.id,
            awi=self.awi,
            max_insurance_premium=self.max_insurance_premium,
            **self.scheduler_params,
        )
        self.scheduler.init(
            simulator=self.simulator,
            products=self.products,
            processes=self.processes,
            producing=self.producing,
            profiles=self.compiled_profiles,
        )

    def respond_to_negotiation_request(
        self, cfp: "CFP", partner: str
    ) -> Optional[Negotiator]:
        if self.awi.is_bankrupt(partner):
            return None
        if self.use_consumer:
            return self.consumer.respond_to_negotiation_request(
                cfp=cfp, partner=partner
            )
        else:
            ufun_ = self.ufun_factory(
                self, self._create_annotation(cfp=cfp, partner=partner)
            )
            ufun_.reserved_value = self.__reserved_value
            neg = self.negotiator_type(
                name=self.name + "*" + partner[:4], **self.negotiator_params, ufun=ufun_
            )
            return neg

    def on_negotiation_success(
        self, contract: Contract, mechanism: NegotiatorMechanismInterface
    ):
        if self.use_consumer:
            self.consumer.on_negotiation_success(contract, mechanism)

    def on_negotiation_failure(
        self,
        partners: List[str],
        annotation: Dict[str, Any],
        mechanism: NegotiatorMechanismInterface,
        state: MechanismState,
    ) -> None:
        if self.use_consumer:
            self.consumer.on_negotiation_failure(partners, annotation, mechanism, state)
        cfp = annotation["cfp"]
        thiscfp = self.awi.bb_query(section="cfps", query=cfp.id, query_keys=True)
        if (
            cfp.publisher != self.id
            and thiscfp is not None
            and len(thiscfp) > 0
            and self.n_neg_trials[cfp.id] < self.n_retrials
        ):
            self.awi.logdebug(f"Renegotiating {self.n_neg_trials[cfp.id]} on {cfp}")
            self.n_neg_trials[cfp.id] += 1
            self.on_new_cfp(cfp=annotation["cfp"])

    def _execute_schedule(self, schedule: ScheduleInfo, contract: Contract) -> None:
        if self.simulator is None:
            raise ValueError("No factory simulator is defined")
        awi: SCMLAWI = self.awi
        total = contract.agreement["unit_price"] * contract.agreement["quantity"]
        product = contract.annotation["cfp"].product
        if contract.annotation["buyer"] == self.id:
            self.simulator.buy(
                product=product,
                quantity=contract.agreement["quantity"],
                price=total,
                t=contract.agreement["time"],
            )
            if total <= 0 or self.max_insurance_premium <= 0.0 or contract is None:
                return
            relative_premium = awi.evaluate_insurance(contract=contract)
            if relative_premium is None:
                return
            premium = relative_premium * total
            if relative_premium <= self.max_insurance_premium:
                self.awi.logdebug(
                    f"{self.name} buys insurance @ {premium:0.02} ({relative_premium:0.02%}) for {str(contract)}"
                )
                awi.buy_insurance(contract=contract)
                self.simulator.pay(premium, self.awi.current_step)
            return
        # I am a seller
        self.simulator.sell(
            product=product,
            quantity=contract.agreement["quantity"],
            price=total,
            t=contract.agreement["time"],
        )
        for job in schedule.jobs:
            if job.action == "run":
                awi.schedule_job(job, contract=contract)
            elif job.action == "stop":
                awi.stop_production(
                    line=job.line,
                    step=job.time,
                    contract=contract,
                    override=job.override,
                )
            else:
                awi.schedule_job(job, contract=contract)
            self.simulator.schedule(job=job, override=False)
        for need in schedule.needs:
            if need.quantity_to_buy <= 0:
                continue
            product_id = need.product
            # self.simulator.reserve(product=product_id, quantity=need.quantity_to_buy, t=need.step)
            if self.use_consumer:
                self.consumer.profiles[product_id].schedule[
                    need.step
                ] += need.quantity_to_buy
                self.consumer.register_product_cfps(
                    p=product_id,
                    t=need.step,
                    profile=self.consumer.profiles[product_id],
                )
                continue
            product = self.products[product_id]
            if product.catalog_price is None:
                price_range = (0.0, 100.0)
            else:
                price_range = (0.5, 1.5 * product.catalog_price)
            # @todo check this. This error is raised sometimes
            if need.step < awi.current_step:
                continue
                # raise ValueError(f'need {need} at {need.step} while running at step {awi.current_step}')
            time = (
                need.step
                if self.max_storage is not None
                else (awi.current_step, need.step)
            )
            cfp = CFP(
                is_buy=True,
                publisher=self.id,
                product=product_id,
                time=time,
                unit_price=price_range,
                quantity=(1, int(1.1 * need.quantity_to_buy)),
            )
            awi.register_cfp(cfp)

    def sign_contract(self, contract: Contract):
        if any(self.awi.is_bankrupt(partner) for partner in contract.partners):
            return None
        signature = self.id
        with temporary_transaction(self.scheduler):
            schedule = self.scheduler.schedule(
                assume_no_further_negotiations=False,
                contracts=[contract],
                ensure_storage_for=self.transportation_delay,
                start_at=self.awi.current_step + 1,
            )

        if self.sign_only_guaranteed_contracts and (
            not schedule.valid or len(schedule.needs) > 1
        ):
            self.awi.logdebug(
                f"{self.name} refused to sign contract {contract.id} because it cannot be scheduled"
            )
            return None
        # if schedule.final_balance <= self.simulator.final_balance:
        #     self.awi.logdebug(f'{self.name} refused to sign contract {contract.id} because it is not expected '
        #                       f'to lead to profit')
        #     return None
        if schedule.valid:
            profit = schedule.final_balance - self.simulator.final_balance
            self.awi.logdebug(
                f"{self.name} singing contract {contract.id} expecting "
                f'{-profit if profit < 0 else profit} {"loss" if profit < 0 else "profit"}'
            )
        else:
            self.awi.logdebug(
                f"{self.name} singing contract {contract.id} expecting breach"
            )
            return None

        self.contract_schedules[contract.id] = schedule
        return signature

    def on_contract_signed(self, contract: Contract):
        if contract.annotation["buyer"] == self.id and self.use_consumer:
            self.consumer.on_contract_signed(contract)
        schedule = self.contract_schedules[contract.id]
        if schedule is not None and schedule.valid:
            self._execute_schedule(schedule=schedule, contract=contract)
        if contract.annotation["buyer"] != self.id or not self.use_consumer:
            for negotiation in self._running_negotiations.values():
                self.notify(
                    negotiation.negotiator,
                    Notification(type="ufun_modified", data=None),
                )

    def _process_buy_cfp(self, cfp: "CFP") -> None:
        if cfp.publisher == self.id:
            return
        if self.awi.is_bankrupt(cfp.publisher):
            return
        if self.simulator is None or not self.can_expect_agreement(
            cfp=cfp, margin=self.negotiation_margin
        ):
            return
        if not self.can_produce(cfp=cfp):
            return
        neg = self.negotiator_type(
            name=self.name + ">" + cfp.publisher[:4], **self.negotiator_params
        )
        ufun = self.ufun_factory(self, self._create_annotation(cfp=cfp))
        ufun.reserved_value = self.__reserved_value
        self.request_negotiation(negotiator=neg, cfp=cfp, ufun=ufun)
        # normalize(, outcomes=cfp.outcomes, infeasible_cutoff=-1)

    def _process_sell_cfp(self, cfp: "CFP"):
        if self.awi.is_bankrupt(cfp.publisher):
            return None
        if self.use_consumer:
            self.consumer.on_new_cfp(cfp=cfp)

    def on_new_cfp(self, cfp: "CFP") -> None:
        if not self.reactive:
            return
        if cfp.satisfies(
            query={"is_buy": True, "products": list(self.producing.keys())}
        ):
            self._process_buy_cfp(cfp)
        if cfp.satisfies(
            query={"is_buy": False, "products": list(self.consuming.keys())}
        ):
            self._process_sell_cfp(cfp)

    def step(self):
        if self.use_consumer:
            self.consumer.step()
        if self.reactive:
            return
        # 0. remove all my CFPs
        # self.awi.bb_remove(section='cfps', query={'publisher': self})

        # respond to interesting CFPs
        # todo: should check time and sort products by interest etc
        cfps = self.awi.bb_query(
            section="cfps", query={"products": self.producing.keys(), "is_buy": True}
        )
        if cfps is None:
            return
        for cfp in cfps.values():
            self._process_buy_cfp(cfp)

    def can_produce(self, cfp: CFP, assume_no_further_negotiations=False) -> bool:
        """Whether or not we can produce the required item in time"""
        if cfp.product not in self.producing.keys():
            return False
        agreement = SCMLAgreement(
            time=cfp.max_time, unit_price=cfp.max_unit_price, quantity=cfp.min_quantity
        )
        min_concluded_at = self.awi.current_step + 1 - int(self.immediate_negotiations)
        min_sign_at = min_concluded_at + self.awi.default_signing_delay
        if cfp.max_time < min_sign_at + 1:  # 1 is minimum time to produce the product
            return False
        with temporary_transaction(self.scheduler):
            schedule = self.scheduler.schedule(
                contracts=[
                    Contract(
                        partners=[self.id, cfp.publisher],
                        agreement=agreement,
                        annotation=self._create_annotation(cfp=cfp),
                        issues=cfp.issues,
                        signed_at=min_sign_at,
                        concluded_at=min_concluded_at,
                    )
                ],
                ensure_storage_for=self.transportation_delay,
                assume_no_further_negotiations=assume_no_further_negotiations,
                start_at=min_sign_at,
            )
        return schedule.valid and self.can_secure_needs(
            schedule=schedule, step=self.awi.current_step
        )

    def can_secure_needs(self, schedule: ScheduleInfo, step: int):
        """
        Finds if it is possible in principle to arrange these needs at the given time.

        Args:
            schedule:
            step:

        Returns:

        """
        needs = schedule.needs
        if len(needs) < 1:
            return True
        for need in needs:
            if need.quantity_to_buy > 0 and need.step < step + 1 - int(
                self.immediate_negotiations
            ):  # @todo check this
                return False
        return True


TotalUtilityFun = Callable[[Collection[Contract]], float]


class NegotiatorUtility(UtilityFunction):
    """The utility function of a negotiator."""

    def __init__(
        self,
        agent: GreedyFactoryManager,
        annotation: Dict[str, Any],
        name: Optional[str] = None,
        avoid_free_sales: bool = True,
        expected_breach_level: float = 0.5,
        **kwargs,
    ):
        if name is None:
            name = (
                (
                    agent.name
                    + "*"
                    + "*".join(_ for _ in annotation["partners"] if _ != agent.id)
                )
                if agent is not None
                else None
            )
        super().__init__(
            name=name,
            **kwargs,
        )
        self.agent = agent
        self.annotation = annotation
        self.avoid_free_sales = avoid_free_sales
        self.expected_breach_level = expected_breach_level

    def _contracts(self, agreements: Iterable[SCMLAgreement]) -> Collection[Contract]:
        """Converts agreements/outcomes into contracts"""
        if self.owner.nmi is None:
            raise ValueError("No annotation is stored (No mechanism info)")
        annotation = self.owner.nmi.annotation
        return [
            Contract(
                partners=annotation["partners"],
                agreement=a,
                annotation=annotation,
                issues=self.owner.nmi.issues,
            )
            for a in agreements
        ]

    def _contract(self, agreement: SCMLAgreement) -> Contract:
        """Converts an agreement/outcome into a contract"""
        annotation = self.annotation
        return Contract(
            partners=annotation["partners"],
            agreement=agreement,
            annotation=annotation,
            issues=annotation["cfp"].issues,
        )

    def _free_sale(self, agreement: SCMLAgreement) -> bool:
        return (
            (
                self.annotation["seller"] == self.agent.id
                and agreement["unit_price"] < 1e-6
            )
            if self.avoid_free_sales
            else False
        )

    def eval(self, outcome: Outcome) -> Optional[Value]:
        if outcome is None:
            return float("-inf")
        if isinstance(outcome, tuple):
            outcome = dict(zip(("quantity", "time", "unit_price"), outcome))
        if isinstance(outcome, dict):
            return self.call(agreement=SCMLAgreement(**outcome))
        if isinstance(outcome, SCMLAgreement):
            return self.call(agreement=outcome)
        raise ValueError(f"Outcome: {outcome} cannot be converted to an SCMLAgreement")

    @abstractmethod
    def call(self, agreement: SCMLAgreement) -> Optional[Value]:
        """Called to evaluate a agreement"""

    def xml(self, issues: List[Issue]) -> str:
        return "NegotiatorUtility has not xml representation"


class PessimisticNegotiatorUtility(NegotiatorUtility):
    """The utility function of a negotiator that assumes other negotiations currently open will fail."""

    def call(self, agreement: SCMLAgreement) -> Optional[Value]:
        """An offer will be a tuple of one value which in turn will be a list of contracts"""
        if self._free_sale(agreement):
            return float("-inf")
        # contracts = self.agent.contracts
        # hypothetical = list(contracts)
        # hypothetical.append(self._contract(agreement))
        hypothetical = [self._contract(agreement)]
        base_util = self.agent.simulator.final_balance
        hypothetical = self.agent.total_utility(hypothetical)
        if hypothetical < 0:
            return float("-inf")
        return hypothetical - base_util


class OptimisticNegotiatorUtility(NegotiatorUtility):
    """The utility function of a negotiator that assumes other negotiations currently open will succeed."""

    def call(self, agreement: SCMLAgreement) -> Optional[Value]:
        if self._free_sale(agreement):
            return float("-inf")
        # contracts = self.agent.contracts
        # hypothetical = list(contracts)
        # hypothetical.append(self._contract(agreement))
        hypothetical = [self._contract(agreement)]
        for negotiation in self.agent.running_negotiations:  # type: ignore
            negotiator = negotiation.negotiator
            current_offer = negotiator.my_last_proposal
            if current_offer is not None:
                hypothetical.append(self._contract(current_offer))
        base_util = self.agent.simulator.final_balance
        hypothetical = self.agent.total_utility(list(hypothetical))
        if hypothetical < 0:
            return float("-inf")
        return hypothetical - base_util


class AveragingNegotiatorUtility(NegotiatorUtility):
    """A utility function that combines optimistic and pessimistic evaluators linearly using adjustable weight"""

    def __init__(
        self,
        agent: GreedyFactoryManager,
        annotation: Dict[str, Any],
        name: Optional[str] = None,
        optimism: float = 0.5,
        avoid_free_sale: bool = True,
    ):
        super().__init__(
            agent=agent,
            annotation=annotation,
            name=name,
            avoid_free_sales=avoid_free_sale,
        )
        self.avoid_free_sales = avoid_free_sale
        self.optimism = optimism
        self.optimistic = OptimisticNegotiatorUtility(
            agent=agent, annotation=annotation, avoid_free_sales=avoid_free_sale
        )
        self.pessimistic = PessimisticNegotiatorUtility(
            agent=agent, annotation=annotation, avoid_free_sales=avoid_free_sale
        )

    def call(self, agreement: SCMLAgreement) -> Optional[Value]:
        if self._free_sale(agreement):
            return float("-inf")
        opt, pess = self.optimistic(agreement), self.pessimistic(agreement)
        if opt is None or pess is None:
            return None
        return self.optimism * opt + (1 - self.optimism) * pess
