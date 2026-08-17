# Ruby Review

- **Use:** Ruby boundary; preserve Ruby version, locked bundle, process, load path,
  runner, and framework/job context.
- **Level 1:** Check syntax, nil/truthiness, symbol/string keys, mutation,
  blocks/enumerators, exceptions, retries, ensure, resources, and dynamic calls.
- **Level 2:** Match class/module, service/result, callback, logging, and spec
  conventions; test validation, failure, retry, transaction, and serialization.
- **Level 3:** Check model/service/job boundaries, globals/thread-locals, callback
  chains, mixins, registries, god objects, and hidden transaction ownership.
- **Proof:** Prefer locked bundle and narrow syntax/lint/spec target.
- **Escalate:** Data corruption, unbounded retry, state leakage, lost exception,
  unsafe execution, or public behavior break.
- **Avoid:** Autocorrect, updates, unsafe app boot/tasks, and Ruby-style opinions.

