# -*- coding: utf-8 -*-
"""=============================================================================
This modules contains the variables and the parameters.
Do not change the variables.
Parameters that can be changed without any risk of damages should be changed
by clicking on the configure sub-menu at the server screen.
If you need to change some parameters below please be sure of what you do,
which means that you should ask to the developer ;-)
============================================================================="""
from datetime import time

# variables --------------------------------------------------------------------
BASELINE = 0
TREATMENTS_NAMES = {0: "Baseline"}

# parameters -------------------------------------------------------------------
TREATMENT = BASELINE
TAUX_CONVERSION = 1
NOMBRE_PERIODES = 10
TAILLE_GROUPES = 4
GROUPES_CHAQUE_PERIODE = False
MONNAIE = u"ecu"
PERIODE_ESSAI = False

TEMPS = time(0, 2, 0)  # hour, minute, second
EVENT_TRIANGLE = 0
EVENT_START = 1
CONTRACT_TRIANGLE = (100, 0)
CONTRACT_STAR = (100, 0)

# DECISION
DECISION_MIN = 0
DECISION_MAX = 100
DECISION_STEP = 1


