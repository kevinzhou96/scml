# required for typing
from collections import defaultdict
import random
import math
from typing import Any, Dict, List, Optional

import numpy as np
from negmas import (
    AgentMechanismInterface,
    Contract,
    Issue,
    Outcome,
    MechanismState,
    Negotiator,
    ResponseType,
)
from negmas.sao import SAONegotiator, SAOState, SAOAMI

from scml.scml2020 import SCML2020Agent, AWI
from scml.scml2020 import TIME, UNIT_PRICE, QUANTITY, NO_COMMAND

__all__ = ["SatisficerAgent"]


class ObedientNegotiator(SAONegotiator):
    """
    A negotiator that controls a single negotiation with a single partner.

    Args:

        selling: Whether this negotiator is engaged on selling or buying
        requested: Whether this negotiator is created to manage a negotiation
                   requested by its owner (as opposed to one that is created
                   to respond to one created by the partner).

    Remarks:

        - This negotiator does nothing. It just passes calls to its owner.

    """

    def __init__(self, *args, selling, requested, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_selling = selling
        self.is_requested = requested

    # =====================
    # Negotiation Callbacks
    # =====================

    def propose(self, state: MechanismState) -> Optional[Outcome]:
        """Simply calls the corresponding method on the owner"""
        return self.owner.propose(state, self.ami, self.is_selling, self.is_requested)

    def respond(self, state: MechanismState, offer: Outcome) -> ResponseType:
        """Simply calls the corresponding method on the owner"""
        return self.owner.respond(
            state, self.ami, offer, self.is_selling, self.is_requested
        )


class SatisficerAgent(SCML2020Agent):
    """
    A simple monolithic agent that tries to *carefully* make small profit
    every step.

    Args:

        target_productivity: The productivity level targeted by the agent defined
                             as the fraction of its lines to be active per step.
        satisfying_profit: A profit amount considered satisfactory. Used when
                           deciding negotiation agenda and signing to decide if
                           a price is a good price (see `_good_price()`). A
                           fraction of the trading price.
        acceptable_loss: A fraction of trading price that the seller/buyer is
                         willing to go under/over the current trading price during
                         negotiation.
        price_range: The total range around the trading price for negotiation agendas.
        concession_rate_price: The exponent of the consession curve for price.
        concession_rate_quantity: The exponent of the consession curve for quantity.
        concession_rate_time: The exponent of the consession curve for time.
        market_share: An integer specifying the expected share of the agent in
                      the market. The agent will assume that it can get up to
                      (market_share / (n_competitors + market_share -1)) of all
                      sales and supplies where `n_competitors` is the number of agents
                      at the same production level. Setting it to 1 means that the agent
                      assumes it will get the same amount of trade as all other agents.
                      Setting it to infinity means that the agent will assume it will take
                      all the trade in the market
        horizon: Time horizon for negotiations. If None, the exogenous_contracts_revelation
                 horizon will be used
    """

    def __init__(
        self,
        *args,
        target_productivity=1.0,
        satisfying_profit=0.15,
        acceptable_loss=0.02,
        price_range=0.4,
        concession_rate_price=1.0,
        concession_rate_quantity=1.0,
        concession_rate_time=1.0,
        market_share=1,
        horizon=5,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.horizon=horizon
        self.satisfying_profit = satisfying_profit
        self.target_productivity = target_productivity
        self.price_range = price_range
        self.ep = concession_rate_price
        self.eq = concession_rate_quantity
        self.et = concession_rate_time
        self.acceptable_loss = acceptable_loss
        self.last_q = defaultdict(int)
        self.last_t = dict()
        self.market_share = market_share

    # =====================
    # Time-Driven Callbacks
    # =====================
    def init(self):
        """Called once"""
        awi: AWI = self.awi
        if self.horizon is None:
            self.horizon = awi.settings.get("horizon", max(1, int(awi.n_steps // 5)))
        self.initial_balance = awi.current_balance
        self.production_cost = float(awi.profile.costs[:, awi.my_input_product].max())
        self.secured_supplies = np.zeros(awi.n_steps, dtype=int)
        self.secured_sales = np.zeros(awi.n_steps, dtype=int)
        self.n_consumers = len(awi.my_consumers)
        self.n_suppliers = len(awi.my_suppliers)
        self.n_competitors = len(awi.all_suppliers[awi.my_output_product])
        assert self.n_consumers > 0 and self.n_suppliers > 0 and self.n_competitors > 0

        # My effective number of lines dependes on production capacity of the market
        self.market_capacity = awi.n_lines * min(
            len(awi.all_consumers[i]) for i in range(awi.n_processes)
        )
        if self.market_share == float("inf"):
            self.market_share = 1.0
        else:
            self.market_share = (self.market_share) / (
                self.n_competitors + self.market_share - 1
            )

    def before_step(self):
        """Called at at the BEGINNING of every production step (day)"""
        awi: AWI = self.awi
        s = awi.current_step
        steps, processes, lines, level = (
            awi.n_steps,
            awi.n_processes,
            awi.n_lines,
            awi.my_input_product,
        )
        prices = awi.trading_prices
        if prices is None:
            prices = awi.catalog_prices

        available_input = int(awi.current_inventory[awi.my_input_product])
        available_output = int(awi.current_inventory[awi.my_output_product])

        # find the time of tirst and last allowed sale and supply
        first_supply = max(s, level)
        last_sale = steps - (processes - level - 1)
        first_sale = first_supply + 1
        last_supply = last_sale - 1

        period = last_sale - first_sale
        assert last_supply - first_supply == period

        # # find the time of first and last sale and supply for my consuemrs and suppliers
        # supplier_first_sale, supplier_last_sale = max(s, level - 1) + 1, last_supply
        # consumer_first_supply, consumer_last_supply = first_sale, last_sale

        # remove any remaining day-specific data structure
        self.tentative_sales = np.zeros(steps, dtype=np.int64)
        self.tentative_supplies = np.zeros(steps, dtype=np.int64)
        self.accepted_sales = np.zeros(steps, dtype=np.int64)
        self.accepted_supplies = np.zeros(steps, dtype=np.int64)

        # find the maximum amount of sales/supplies that can happen in this market
        # in the future (for me)
        capacity = min(self.market_capacity, lines)
        future_sales = int(
            0.5 + capacity * self.market_share * period * self.target_productivity
        )

        # find total target sales and supplies to the end of the simulation.
        # I need to sell everything in my inventory but buy only what is not
        # already in it.
        self.target_sales = future_sales + available_output + available_input
        self.target_supplies = self.target_sales - available_input

        # self.max_sales = self.secured_sales.copy()
        # self.max_supplies = self.secured_supplies.copy()
        self.max_sales = np.zeros(steps, dtype=np.int64)
        self.max_supplies = np.zeros(steps, dtype=np.int64)

        if period > 0:
            prev = 0
            for t in range(1, steps):
                limit = (
                    future_sales + available_output + (0 if t <= s else available_input)
                )
                self.max_sales[t] = min(lines, limit - prev)
                if self.max_sales[t] >= self.target_sales - prev:
                    break
                prev += self.max_sales[t]
            self.max_sales[last_sale - 1 :] = self.max_sales[last_sale - 1]
            for t in range(0, steps - 1):
                self.max_supplies[t] = self.max_sales[t + 1:].sum()
            self.max_sales -= self.secured_sales
            self.max_supplies -= self.secured_supplies
            self.max_sales = self.max_sales.cumsum()
            self.max_supplies = self.max_supplies.cumsum()
            self.max_supplies = np.minimum(
                self.max_supplies,
                int(awi.current_balance // prices[awi.my_input_product]),
            )

        # TODO use minimums to make sure that I sell everything at the end and I get all my needs for production
        # items here should be sold/bought at any price or at least with some margin of loss
        self.min_sales = np.zeros(steps, dtype=np.int64)
        self.min_supplies = np.zeros(steps, dtype=np.int64)

        # specify that for any agent, we will strart conceding on price first
        self.next_concession_dim = defaultdict(lambda: random.randint(0, 2))

    def step(self):
        """Called at the end of the day. Will request all negotiations"""
        awi: AWI = self.awi
        s = awi.current_step
        steps = awi.n_steps
        prices = awi.trading_prices
        if prices is None:
            prices = awi.catalog_prices

        self.do_production()


        # request negotiations
        for product, selling, partners, limit in (
            (
                awi.my_input_product,
                False,
                awi.my_suppliers,
                self.max_supplies[s:].max(),
            ),
            (
                awi.my_output_product,
                True,
                awi.my_consumers,
                self.max_sales[s:].max(),
            ),
        ):
            # do nothing if the limit is zero
            if limit < 1:
                continue
            # do nothing if the partners are system agents
            if selling and product >= awi.n_processes:
                continue
            if not selling and product < 1:
                continue

            # decide the negotiation issue limits
            # ===================================

            # for quantity, just set the maximum to the limit
            qrange = (1, limit)

            # for time, we start at this step if buying else next step and
            # end at the last step in which I should do trade
            t0 = s if not selling else s + 1
            if not selling:
                last_step = awi.n_steps - awi.n_processes - awi.my_input_product - 2
            else:
                last_step = awi.n_steps - 1
            trange = (t0, min(t0 + self.horizon, last_step))

            # If no time is acceptable, just do not request negotiations
            if trange[0] > trange[1]:
                continue

            # Calcualt a price in the middle of the price range I am willing to
            #  offer by comparing two prices
            # 1. The selling/buyg price that gives me a satisfactory profit given
            #    the current trading price for input/output (correspondingly)
            # 2. The current trading price of my output/input in case of selling/buying
            # If the two options are not equal, resolve to my advantage
            price = (
                max(
                    prices[product],
                    (1 + self.satisfying_profit)
                    * (prices[product - 1] + self.production_cost),
                )
                if selling
                else min(
                    prices[product],
                    (1 - self.satisfying_profit)
                    * (prices[product + 1] - self.production_cost),
                )
            )

            # set the price ragne so that the price I prefer is in the middle
            dp = prices[product] * self.price_range / 2.0
            urange = (
                int(price - dp),
                int(price + dp + 0.5),
            )
            # Request the negotiations
            awi.request_negotiations(
                not selling,
                product,
                qrange,
                urange,
                trange,
                None,
                [
                    ObedientNegotiator(
                        selling=selling, requested=True, name=f"{self.id}>{_}"
                    )
                    for _ in partners
                ],
                partners,
            )

    # ================================
    # Negotiation Control and Feedback
    # ================================

    def respond_to_negotiation_request(
        self,
        initiator: str,
        issues: List[Issue],
        annotation: Dict[str, Any],
        mechanism: AgentMechanismInterface,
    ) -> Optional[Negotiator]:
        """Called whenever an agent requests a negotiation with you.
        Return either a negotiator to accept or None (default) to reject it"""
        return ObedientNegotiator(
            selling=annotation["seller"] == self.id,
            requested=False,
            name=f"{initiator}>{self.id}",
        )

    # =============================
    # Contract Control and Feedback
    # =============================

    def sign_all_contracts(self, contracts: List[Contract]) -> List[Optional[str]]:
        """
        Called to ask you to sign all contracts that were concluded in
        one step (day)
        """
        signatures: List[Optional[str]] = [None] * len(contracts)
        awi: AWI = self.awi

        # separate sell and buy contracts and sort them with the better price
        # first (ties are broken by smallest quantity first)
        sell_contracts = sorted(
            [
                (i, _)
                for i, _ in enumerate(contracts)
                if _.annotation["seller"] == self.id
            ],
            key=lambda x: (-x[1].agreement["unit_price"], x[1].agreement["quantity"]),
        )
        buy_contracts = sorted(
            [
                (i, _)
                for i, _ in enumerate(contracts)
                if _.annotation["seller"] != self.id
            ],
            key=lambda x: (x[1].agreement["unit_price"], x[1].agreement["quantity"]),
        )
        bought, sold = np.zeros(awi.n_steps), np.zeros(awi.n_steps)
        total_bought = total_sold = 0
        # breakpoint()
        for i, c in buy_contracts:
            # If I already signed above my total needs, do not sign any more.
            if total_bought >= self.target_supplies:
                break
            q, u, t = (
                c.agreement["quantity"],
                c.agreement["unit_price"],
                c.agreement["time"],
            )
            # If I already signed above my total needs FOR THE DAY, do not sign any more.
            if bought[t] >= self.max_supplies[t]:
                break
            # End if prices go too high
            if not self._is_good_price(False, u, slack=self.satisfying_profit * 1.5):
                continue
            signatures[i] = self.id
            bought[t] += q

        for i, c in sell_contracts:
            # If I already signed above my total needs, do not sign any more.
            if total_sold >= self.target_supplies:
                break
            q, u, t = (
                c.agreement["quantity"],
                c.agreement["unit_price"],
                c.agreement["time"],
            )
            # If I already signed above my total needs FOR THE DAY, do not sign any more.
            if sold[t] >= self.max_supplies[t]:
                break
            # End if prices go too high
            if not self._is_good_price(True, u, slack=self.satisfying_profit * 1.5):
                continue
            signatures[i] = self.id
            sold[t] += q

        return signatures

    def on_contracts_finalized(
        self,
        signed: List[Contract],
        cancelled: List[Contract],
        rejectors: List[List[str]],
    ) -> None:
        """Called to inform you about the final status of all contracts in
        a step (day)"""
        awi: AWI = self.awi
        sell_contracts = [_ for _ in signed if _.annotation["seller"] == self.id]
        buy_contracts = [_ for _ in signed if _.annotation["seller"] != self.id]

        for c in buy_contracts:
            # If I already signed above my total needs, do not sign any more.
            q, t = (
                c.agreement["quantity"],
                c.agreement["time"],
            )
            self.secured_supplies[t] += q
            self.accepted_supplies[t] -= q

        for c in sell_contracts:
            # If I already signed above my total needs, do not sign any more.
            q, t = (
                c.agreement["quantity"],
                c.agreement["time"],
            )
            self.secured_sales[t] += q
            self.accepted_sales[t] -= q

    # ====================
    # Production Callbacks
    # ====================

    def do_production(self) -> int:
        # breakpoint()
        awi: AWI = self.awi
        commands = NO_COMMAND * np.ones(awi.n_lines, dtype=int)

        # find how much input material do we have
        inputs = min(awi.state.inventory[awi.my_input_product], len(commands))

        # register production commands
        commands[:inputs] = awi.my_input_product
        commands[inputs:] = NO_COMMAND
        awi.set_commands(commands)
        return inputs

    # =====================
    # Negotiation functions
    # =====================

    def propose(
        self, state: SAOState, ami: SAOAMI, is_selling: bool, is_requested: bool
    ):
        """
        Used to propose to the opponent

        Args:
            state: mechanism state including current round
            ami: Agent-mechanism-interface for accessing the negotiation mechanism
            offer: The offer proposed by the partner
            is_selling: Whether the agent is selling to this partner
            is_requested: Whether the agent requested this negotiation
        """
        # remove the last offer we sent to the partner from the tentative list
        # because it is implicitly rejected by the partner.
        partner = [_ for _ in ami.agent_ids if _ != self.id][0]
        self._remove_tentative_offer(is_selling, partner)

        awi: AWI = self.awi
        prices = awi.trading_prices
        if prices is None:
            prices = awi.catalog_prices

        t0, t1 = ami.issues[TIME].min_value, ami.issues[TIME].max_value
        q0, q1 = ami.issues[QUANTITY].min_value, ami.issues[QUANTITY].max_value
        p0, p1 = ami.issues[UNIT_PRICE].min_value, ami.issues[UNIT_PRICE].max_value

        # Select an issue to conceed on and the concession ratio which always
        # goes from 1 to 0 over negotiation time
        cdim = self.next_concession_dim[partner]
        r = [
            1
            - math.pow(
                state.step / (awi.n_steps - 1)
                if cdim == i
                else max(0, state.step - 1) / (awi.n_steps - 1),
                self.eq,
            )
            for i in range(3)
        ]
        self.next_concession_dim[partner] = random.randint(0, 2)

        # calculate  a price p that is good enough given the number of rounds
        # remaining. This is a time-based concession strategy on price.
        if is_selling:
            tentative, accepted, max_quantity, min_quantity = (
                self.tentative_sales,
                self.accepted_sales,
                self.max_sales,
                self.min_sales,
            )
            n_partners = self.n_consumers
            accaptable_price = prices[awi.my_output_product] * (
                1 - self.acceptable_loss
            )
            p = max((p1 - accaptable_price) * r[UNIT_PRICE] + accaptable_price, p0)
        else:
            tentative, accepted, max_quantity, min_quantity = (
                self.tentative_supplies,
                self.accepted_supplies,
                self.max_supplies,
                self.min_supplies,
            )
            n_partners = self.n_suppliers
            accaptable_price = prices[awi.my_input_product] * (1 + self.acceptable_loss)
            p = min((accaptable_price - p0) * r[UNIT_PRICE] + accaptable_price, p1)
            r[TIME] = 1 - r[TIME]

        # find the range of quantities that I can accept within the time we are
        # negotiating about
        max_quantity, min_quantity = (
            max_quantity[t0 : t1 + 1] - tentative[t0 : t1 + 1] - accepted[t0 : t1 + 1],
            min_quantity[t0 : t1 + 1],
        )
        max_quantity[max_quantity > q1] = q1
        min_quantity[min_quantity < q0] = q0

        # If we have no quantities to consider, end
        if len(min_quantity) < 1 or len(max_quantity) < 1:
            return None

        # find all valid times
        ts = [
            _
            for _ in range(t0, t1 + 1)
            if max_quantity[_ - t0] >= q0
            and max_quantity[_ - t0] >= min_quantity[_ - t0]
        ]

        # If we have not valid time, end the round offering nothing.
        n_times = len(ts)
        if n_times < 1:
            return None

        # select a time in the valid range (this is an index in the quantites
        # array)
        t = ts[max(0, min(n_times - 1, int(0.5 + n_times * r[TIME])))] - t0

        # select a quantity in the valid range for the selected time
        if max_quantity[t] == min_quantity[t]:
            q = max_quantity[t]
        else:
            q = max(
                q0,
                min_quantity[t],
                min(
                    max_quantity[t],
                    int((max_quantity[t] - min_quantity[t]) * r[QUANTITY])
                    + min_quantity[t],
                ),
            )

        offer = [0, 0, 0]
        offer[TIME], offer[QUANTITY], offer[UNIT_PRICE] = (
            min(t1, max(t0, t + t0)),
            min(q1, max(q0, int(q))),
            min(p1, max(p0, int(p + 0.5))),
        )

        partner = [_ for _ in ami.agent_ids if _ != self.id][0]

        tentative[t:] += q
        self.last_q[partner] = q
        self.last_t[partner] = t

        return tuple(offer)

    def respond(
        self,
        state: SAOState,
        ami: SAOAMI,
        offer: Outcome,
        is_selling: bool,
        is_requested: bool,
    ):
        """
        Responds to an offer from one partner.

        Args:
            state: mechanism state including current round
            ami: Agent-mechanism-interface for accessing the negotiation mechanism
            offer: The offer proposed by the partner
            is_selling: Whether the agent is selling to this partner
            is_requested: Whether the agent requested this negotiation

        Remarks:

            - The main idea is to accept offers that are within the quantity limits
              for the delivery day if its price is good enough for the current stage
              of the negotiation.
            - During negotiation, the agent starts accepting highest/lowest prices
              for selling/buying and gradually conceeds to the minimally acceptable
              price (`good_price`) defined as being `acceptable_loss` above/below
              the trading price for buying/selling.

        """
        # Find the price range for this negotiation
        p0, p1 = ami.issues[UNIT_PRICE].min_value, ami.issues[UNIT_PRICE].max_value

        # Find current trading prices (catalog price if trading prices are not available)
        awi: AWI = self.awi
        prices = awi.trading_prices
        if prices is None:
            prices = awi.catalog_prices

        # Find the last offer we sent to this partner
        partner = [_ for _ in ami.agent_ids if _ != self.id][0]

        # read limits of quantities and our tentative offers based on whether
        # we are selling/buygin
        if is_selling:
            tentative, accepted, max_quantity, min_quantity = (
                self.tentative_sales,
                self.accepted_sales,
                self.max_sales,
                self.min_sales,
            )
            worst_acceptable_price = (
                prices[awi.my_output_product] * (1 - self.acceptable_loss)
                if ami.annotation["caller"] != self.id
                else p0
            )
        else:
            tentative, accepted, max_quantity, min_quantity = (
                self.tentative_supplies,
                self.accepted_supplies,
                self.max_supplies,
                self.min_supplies,
            )
            worst_acceptable_price = (
                prices[awi.my_input_product] * (1 + self.acceptable_loss)
                if ami.annotation["caller"] != self.id
                else p1
            )

        # parse the offer
        q, u, t = (
            offer[QUANTITY],
            offer[UNIT_PRICE],
            offer[TIME],
        )

        # r will go from one to zero over the negotiation time and controls our
        # concession
        r = 1 - math.pow(state.relative_time, self.ep)

        if is_selling:
            # If selling we conceed down from the highest price
            p = (p1 - worst_acceptable_price) * r + worst_acceptable_price
        else:
            # If buing we conceed up from the lowest price
            p = (worst_acceptable_price - p0) * r + worst_acceptable_price

        # if the quantity offers is not within the range we want for this time-step
        # reject the offer
        if q + tentative[t] + accepted[t] > max_quantity[t] or q < min_quantity[t]:
            return ResponseType.REJECT_OFFER

        # if price is OK accept the offer
        if (is_selling and u >= p) or (not is_selling and u <= p):
            accepted[t:] += q
            return ResponseType.ACCEPT_OFFER
        # otherwise, reject it
        return ResponseType.REJECT_OFFER

    def on_negotiation_failure(self, partners, annotation, mechanism, state):
        """
        Called when a negotiation fails

        Remarks:
            - removes my standing tentative offer for this negotiation if any

        """
        partner = [_ for _ in mechanism.agent_ids][0]
        self._remove_tentative_offer(annotation["seller"]==self.id, partner)

    def on_negotiation_success(self, contract, mechanism):
        """
        Called when a negotiation fails

        Remarks:
            - removes my standing tentative offer for this negotiation if any
            - adds the agreed quantity in the appropriate times of `accepted`.
              It will be moved later to `secured`

        """
        partner = [_ for _ in contract.partners if _ != self.id][0]
        self._remove_tentative_offer(contract.annotation["seller"]==self.id, partner)

        selling = contract.annotation["seller"] == self.id
        accepted = self.accepted_sales if selling else self.accepted_supplies
        accepted[contract.agreement["time"]:] += contract.agreement["quantity"]

    # ================
    # Helper Functions
    # ================

    def _remove_tentative_offer(self, selling, partner):
        """
        Removes my last offer from the tentative offers
        """
        last_t = self.last_t.pop(partner, None)
        tentative = self.tentative_sales if selling else self.tentative_supplies
        if last_t is None:
            return
        tentative[last_t:] -= self.last_q[partner]
        del self.last_q[partner]


    def _is_good_price(self, is_selling: bool, u: float, slack: float = 0.0):
        awi: AWI = self.awi
        prices = awi.trading_prices
        if prices is None:
            prices = awi.catalog_prices
        if is_selling:
            return u > (1 + self.satisfying_profit - slack) * (
                prices[awi.my_input_product] + self.production_cost
            )
        return u < (1 - self.satisfying_profit + slack) * (
            prices[awi.my_output_product] - self.production_cost
        )