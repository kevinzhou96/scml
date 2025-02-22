IndDecentralizingAgent
======================

.. currentmodule:: scml.scml2020

.. autoclass:: IndDecentralizingAgent
   :show-inheritance:

   .. rubric:: Attributes Summary

   .. autosummary::

      ~IndDecentralizingAgent.accepted_negotiation_requests
      ~IndDecentralizingAgent.awi
      ~IndDecentralizingAgent.crisp_ufun
      ~IndDecentralizingAgent.has_cardinal_preferences
      ~IndDecentralizingAgent.has_preferences
      ~IndDecentralizingAgent.has_ufun
      ~IndDecentralizingAgent.id
      ~IndDecentralizingAgent.initialized
      ~IndDecentralizingAgent.internal_state
      ~IndDecentralizingAgent.name
      ~IndDecentralizingAgent.negotiation_requests
      ~IndDecentralizingAgent.preferences
      ~IndDecentralizingAgent.prob_ufun
      ~IndDecentralizingAgent.requested_negotiations
      ~IndDecentralizingAgent.reserved_outcome
      ~IndDecentralizingAgent.reserved_value
      ~IndDecentralizingAgent.running_negotiations
      ~IndDecentralizingAgent.short_type_name
      ~IndDecentralizingAgent.type_name
      ~IndDecentralizingAgent.type_postfix
      ~IndDecentralizingAgent.ufun
      ~IndDecentralizingAgent.unsigned_contracts
      ~IndDecentralizingAgent.use_trading
      ~IndDecentralizingAgent.uuid

   .. rubric:: Methods Summary

   .. autosummary::

      ~IndDecentralizingAgent.acceptable_unit_price
      ~IndDecentralizingAgent.before_step
      ~IndDecentralizingAgent.can_be_produced
      ~IndDecentralizingAgent.checkpoint
      ~IndDecentralizingAgent.checkpoint_info
      ~IndDecentralizingAgent.confirm_production
      ~IndDecentralizingAgent.create
      ~IndDecentralizingAgent.create_negotiation_request
      ~IndDecentralizingAgent.create_ufun
      ~IndDecentralizingAgent.from_checkpoint
      ~IndDecentralizingAgent.from_config
      ~IndDecentralizingAgent.init
      ~IndDecentralizingAgent.init_
      ~IndDecentralizingAgent.negotiator
      ~IndDecentralizingAgent.notify
      ~IndDecentralizingAgent.on_agent_bankrupt
      ~IndDecentralizingAgent.on_contract_breached
      ~IndDecentralizingAgent.on_contract_cancelled
      ~IndDecentralizingAgent.on_contract_cancelled_
      ~IndDecentralizingAgent.on_contract_executed
      ~IndDecentralizingAgent.on_contract_signed
      ~IndDecentralizingAgent.on_contract_signed_
      ~IndDecentralizingAgent.on_contracts_finalized
      ~IndDecentralizingAgent.on_event
      ~IndDecentralizingAgent.on_failures
      ~IndDecentralizingAgent.on_neg_request_accepted
      ~IndDecentralizingAgent.on_neg_request_accepted_
      ~IndDecentralizingAgent.on_neg_request_rejected
      ~IndDecentralizingAgent.on_neg_request_rejected_
      ~IndDecentralizingAgent.on_negotiation_failure
      ~IndDecentralizingAgent.on_negotiation_failure_
      ~IndDecentralizingAgent.on_negotiation_success
      ~IndDecentralizingAgent.on_negotiation_success_
      ~IndDecentralizingAgent.on_preferences_changed
      ~IndDecentralizingAgent.on_simulation_step_ended
      ~IndDecentralizingAgent.on_simulation_step_started
      ~IndDecentralizingAgent.predict_quantity
      ~IndDecentralizingAgent.read_config
      ~IndDecentralizingAgent.respond_to_negotiation_request
      ~IndDecentralizingAgent.respond_to_negotiation_request_
      ~IndDecentralizingAgent.respond_to_renegotiation_request
      ~IndDecentralizingAgent.set_preferences
      ~IndDecentralizingAgent.set_renegotiation_agenda
      ~IndDecentralizingAgent.sign_all_contracts
      ~IndDecentralizingAgent.sign_contract
      ~IndDecentralizingAgent.spawn
      ~IndDecentralizingAgent.spawn_object
      ~IndDecentralizingAgent.start_negotiations
      ~IndDecentralizingAgent.step
      ~IndDecentralizingAgent.step_
      ~IndDecentralizingAgent.target_quantities
      ~IndDecentralizingAgent.target_quantity
      ~IndDecentralizingAgent.to_dict
      ~IndDecentralizingAgent.trade_prediction_before_step
      ~IndDecentralizingAgent.trade_prediction_init
      ~IndDecentralizingAgent.trade_prediction_step

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
   .. automethod:: can_be_produced
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
   .. automethod:: predict_quantity
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
