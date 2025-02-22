BuyCheapSellExpensiveAgent
==========================

.. currentmodule:: scml.scml2020

.. autoclass:: BuyCheapSellExpensiveAgent
   :show-inheritance:

   .. rubric:: Attributes Summary

   .. autosummary::

      ~BuyCheapSellExpensiveAgent.accepted_negotiation_requests
      ~BuyCheapSellExpensiveAgent.awi
      ~BuyCheapSellExpensiveAgent.crisp_ufun
      ~BuyCheapSellExpensiveAgent.has_cardinal_preferences
      ~BuyCheapSellExpensiveAgent.has_preferences
      ~BuyCheapSellExpensiveAgent.has_ufun
      ~BuyCheapSellExpensiveAgent.id
      ~BuyCheapSellExpensiveAgent.initialized
      ~BuyCheapSellExpensiveAgent.internal_state
      ~BuyCheapSellExpensiveAgent.name
      ~BuyCheapSellExpensiveAgent.negotiation_requests
      ~BuyCheapSellExpensiveAgent.preferences
      ~BuyCheapSellExpensiveAgent.prob_ufun
      ~BuyCheapSellExpensiveAgent.requested_negotiations
      ~BuyCheapSellExpensiveAgent.reserved_outcome
      ~BuyCheapSellExpensiveAgent.reserved_value
      ~BuyCheapSellExpensiveAgent.running_negotiations
      ~BuyCheapSellExpensiveAgent.short_type_name
      ~BuyCheapSellExpensiveAgent.type_name
      ~BuyCheapSellExpensiveAgent.type_postfix
      ~BuyCheapSellExpensiveAgent.ufun
      ~BuyCheapSellExpensiveAgent.unsigned_contracts
      ~BuyCheapSellExpensiveAgent.use_trading
      ~BuyCheapSellExpensiveAgent.uuid

   .. rubric:: Methods Summary

   .. autosummary::

      ~BuyCheapSellExpensiveAgent.acceptable_unit_price
      ~BuyCheapSellExpensiveAgent.before_step
      ~BuyCheapSellExpensiveAgent.checkpoint
      ~BuyCheapSellExpensiveAgent.checkpoint_info
      ~BuyCheapSellExpensiveAgent.confirm_production
      ~BuyCheapSellExpensiveAgent.create
      ~BuyCheapSellExpensiveAgent.create_negotiation_request
      ~BuyCheapSellExpensiveAgent.create_ufun
      ~BuyCheapSellExpensiveAgent.from_checkpoint
      ~BuyCheapSellExpensiveAgent.from_config
      ~BuyCheapSellExpensiveAgent.init
      ~BuyCheapSellExpensiveAgent.init_
      ~BuyCheapSellExpensiveAgent.negotiator
      ~BuyCheapSellExpensiveAgent.notify
      ~BuyCheapSellExpensiveAgent.on_agent_bankrupt
      ~BuyCheapSellExpensiveAgent.on_contract_breached
      ~BuyCheapSellExpensiveAgent.on_contract_cancelled
      ~BuyCheapSellExpensiveAgent.on_contract_cancelled_
      ~BuyCheapSellExpensiveAgent.on_contract_executed
      ~BuyCheapSellExpensiveAgent.on_contract_signed
      ~BuyCheapSellExpensiveAgent.on_contract_signed_
      ~BuyCheapSellExpensiveAgent.on_contracts_finalized
      ~BuyCheapSellExpensiveAgent.on_event
      ~BuyCheapSellExpensiveAgent.on_failures
      ~BuyCheapSellExpensiveAgent.on_neg_request_accepted
      ~BuyCheapSellExpensiveAgent.on_neg_request_accepted_
      ~BuyCheapSellExpensiveAgent.on_neg_request_rejected
      ~BuyCheapSellExpensiveAgent.on_neg_request_rejected_
      ~BuyCheapSellExpensiveAgent.on_negotiation_failure
      ~BuyCheapSellExpensiveAgent.on_negotiation_failure_
      ~BuyCheapSellExpensiveAgent.on_negotiation_success
      ~BuyCheapSellExpensiveAgent.on_negotiation_success_
      ~BuyCheapSellExpensiveAgent.on_preferences_changed
      ~BuyCheapSellExpensiveAgent.on_simulation_step_ended
      ~BuyCheapSellExpensiveAgent.on_simulation_step_started
      ~BuyCheapSellExpensiveAgent.read_config
      ~BuyCheapSellExpensiveAgent.respond_to_negotiation_request
      ~BuyCheapSellExpensiveAgent.respond_to_negotiation_request_
      ~BuyCheapSellExpensiveAgent.respond_to_renegotiation_request
      ~BuyCheapSellExpensiveAgent.set_preferences
      ~BuyCheapSellExpensiveAgent.set_renegotiation_agenda
      ~BuyCheapSellExpensiveAgent.sign_all_contracts
      ~BuyCheapSellExpensiveAgent.sign_contract
      ~BuyCheapSellExpensiveAgent.spawn
      ~BuyCheapSellExpensiveAgent.spawn_object
      ~BuyCheapSellExpensiveAgent.start_negotiations
      ~BuyCheapSellExpensiveAgent.step
      ~BuyCheapSellExpensiveAgent.step_
      ~BuyCheapSellExpensiveAgent.target_quantities
      ~BuyCheapSellExpensiveAgent.target_quantity
      ~BuyCheapSellExpensiveAgent.to_dict
      ~BuyCheapSellExpensiveAgent.trade_prediction_before_step
      ~BuyCheapSellExpensiveAgent.trade_prediction_init
      ~BuyCheapSellExpensiveAgent.trade_prediction_step

   .. rubric:: Attributes Documentation

   .. autoattribute:: accepted_negotiation_requests
   .. autoattribute:: awi
   .. autoattribute:: crisp_ufun
   .. autoattribute:: has_cardinal_preferences
   .. autoattribute:: has_preferences
   .. autoattribute:: has_ufun
   .. autoattribute:: id
   .. autoattribute:: initialized
   .. autoattribute:: internal_state
   .. autoattribute:: name
   .. autoattribute:: negotiation_requests
   .. autoattribute:: preferences
   .. autoattribute:: prob_ufun
   .. autoattribute:: requested_negotiations
   .. autoattribute:: reserved_outcome
   .. autoattribute:: reserved_value
   .. autoattribute:: running_negotiations
   .. autoattribute:: short_type_name
   .. autoattribute:: type_name
   .. autoattribute:: type_postfix
   .. autoattribute:: ufun
   .. autoattribute:: unsigned_contracts
   .. autoattribute:: use_trading
   .. autoattribute:: uuid

   .. rubric:: Methods Documentation

   .. automethod:: acceptable_unit_price
   .. automethod:: before_step
   .. automethod:: checkpoint
   .. automethod:: checkpoint_info
   .. automethod:: confirm_production
   .. automethod:: create
   .. automethod:: create_negotiation_request
   .. automethod:: create_ufun
   .. automethod:: from_checkpoint
   .. automethod:: from_config
   .. automethod:: init
   .. automethod:: init_
   .. automethod:: negotiator
   .. automethod:: notify
   .. automethod:: on_agent_bankrupt
   .. automethod:: on_contract_breached
   .. automethod:: on_contract_cancelled
   .. automethod:: on_contract_cancelled_
   .. automethod:: on_contract_executed
   .. automethod:: on_contract_signed
   .. automethod:: on_contract_signed_
   .. automethod:: on_contracts_finalized
   .. automethod:: on_event
   .. automethod:: on_failures
   .. automethod:: on_neg_request_accepted
   .. automethod:: on_neg_request_accepted_
   .. automethod:: on_neg_request_rejected
   .. automethod:: on_neg_request_rejected_
   .. automethod:: on_negotiation_failure
   .. automethod:: on_negotiation_failure_
   .. automethod:: on_negotiation_success
   .. automethod:: on_negotiation_success_
   .. automethod:: on_preferences_changed
   .. automethod:: on_simulation_step_ended
   .. automethod:: on_simulation_step_started
   .. automethod:: read_config
   .. automethod:: respond_to_negotiation_request
   .. automethod:: respond_to_negotiation_request_
   .. automethod:: respond_to_renegotiation_request
   .. automethod:: set_preferences
   .. automethod:: set_renegotiation_agenda
   .. automethod:: sign_all_contracts
   .. automethod:: sign_contract
   .. automethod:: spawn
   .. automethod:: spawn_object
   .. automethod:: start_negotiations
   .. automethod:: step
   .. automethod:: step_
   .. automethod:: target_quantities
   .. automethod:: target_quantity
   .. automethod:: to_dict
   .. automethod:: trade_prediction_before_step
   .. automethod:: trade_prediction_init
   .. automethod:: trade_prediction_step
