from mjlab.utils.lab_api.tasks.importer import import_packages

_BLACKLIST_PKGS = ["utils", ".mdp"]

import_packages(__name__, _BLACKLIST_PKGS)
import furo_rl_locomotion_mjlab.config  # noqa: F401
