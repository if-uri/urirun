"""Compatibility facade for generic contract export."""
from urirun_contract.contract_export import *  # noqa: F401,F403


if __name__ == "__main__":
    from urirun_contract.contract_export import main
    raise SystemExit(main())
