"""Layer 3 strategy evaluators.

One Python module per subcategory at
`app/evaluators/<CATEGORY_CODE>/<SUB_CODE>.py`. Each module exports a
class named `Evaluator` that conforms to the `Evaluator` protocol in
`app.evaluators._base`.

Evaluator modules never hardcode model strings, rates, thresholds, form
numbers, or statutory cites. All such values come from
`app.config.rules`, `app.config.authorities`, and `app.config.forms`.

The orchestrator (Layer 4) discovers evaluators through
`app.evaluators._registry`. Orchestrator tests iterate the full registry
against every fixture scenario.
"""
