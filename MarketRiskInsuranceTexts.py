# -*- coding: utf-8 -*-
"""
This module contains the texts of the part (server and remote)
"""

from util.utiltools import get_pluriel
import MarketRiskInsuranceParams as pms
# from util.utili18n import le2mtrans
import os
import configuration.configparam as params
import gettext
import logging

logger = logging.getLogger("le2m")
try:
    localedir = os.path.join(params.getp("PARTSDIR"), "MarketRiskInsurance",
                             "locale")
    trans_MRI = gettext.translation(
      "MarketRiskInsurance", localedir, languages=[params.getp("LANG")]).ugettext
except (AttributeError, IOError):
    logger.critical(u"Translation file not found")
    trans_MRI = lambda x: x  # if there is an error, no translation


def get_histo_head():
    return [trans_MRI(u"Period"), trans_MRI(u"Decision"),
            trans_MRI(u"Period\npayoff"), trans_MRI(u"Cumulative\npayoff")]


def get_text_explanation():
    return trans_MRI(u"")


def get_text_summary(period_content):
    txt = trans_MRI(u"Summary text")
    return txt


