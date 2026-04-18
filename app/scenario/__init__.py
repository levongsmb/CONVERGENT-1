"""app.scenario — Layer 2 client scenario models, validators, and fixtures.

Evaluators (Layer 3) and the orchestrator (Layer 4) consume `ClientScenario`
instances constructed from firm-authored YAML fixtures or from a future
intake UI. All dollar fields are `Decimal`. All dates are `date`. Enums are
strict string enums used in YAML through their string values.

Public surface:
  - app.scenario.models: ClientScenario, Identity, Income, Entity, Asset,
    Deductions, PlanningContext, PriorYearContext, enums, sub-models.
  - app.scenario.validators: cross-fixture consistency checks beyond
    the model-level validators.
  - app.scenario.fixtures: the seven canonical planning scenarios.
"""
