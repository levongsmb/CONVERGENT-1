"""Hot-swappable configuration layer.

Code does not reference model strings, tax rates, form numbers, or statutory
cites directly. Code references task classes and lookup keys. Model strings,
rates, thresholds, form numbers, and statutory cites live in the config/
directory at the repository root. Swaps happen in config/; code is unchanged.

Public loaders:
  - app.config.router.get_llm_config(task_class)
  - app.config.rules.get_rule(key, year)
  - app.config.authorities.get_authority(id, year)
  - app.config.forms.get_form(id, year)
  - app.config.prompts.render(template_name, **vars)
  - app.config.validate.validate_all() (pre-commit hook entry point)
"""
