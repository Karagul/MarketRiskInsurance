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


def get_histo_vars():
    return ["MRI_period", "MRI_endowment",
            "MRI_triangle_sum_of_purchase", "MRI_triangle_number_of_purchase",
            "MRI_triangle_sum_of_sell", "MRI_triangle_number_of_sell",
            "MRI_star_sum_of_purchase", "MRI_star_number_of_purchase",
            "MRI_star_sum_of_sell", "MRI_star_number_of_sell",
            "MRI_event", "MRI_event_balance", "MRI_periodpayoff"]


def get_histo_head():
    return [trans_MRI(u"Period"),
            trans_MRI(u"Endowment"),
            trans_MRI(u"Triangle\npurchases\n(amount)"),
            trans_MRI(u"Triangle\npurchases\n(number)"),
            trans_MRI(u"Triangle\nsells\n(amount)"),
            trans_MRI(u"Triangle\nsells\n(number)"),
            trans_MRI(u"Star\npurchases\n(amount)"),
            trans_MRI(u"Star\npurchases\n(number)"),
            trans_MRI(u"Star\nsells\n(amount)"),
            trans_MRI(u"Star\nsells\n(number)"),
            trans_MRI(u"Event"), trans_MRI(u"Event\nbalance"),
            trans_MRI(u"Period\npayoff")]


def get_text_explanation():
    return trans_MRI(u"")


def get_text_summary(period_content):
    logger.debug(period_content)
    txt = trans_MRI(u"On the triangle market, you've made {} ({}) and {} ({}).").format(
        get_pluriel(period_content["MRI_triangle_number_of_purchase"],
                    trans_MRI(u"purchase")),
        get_pluriel(period_content["MRI_triangle_sum_of_purchase"], pms.MONNAIE),
        get_pluriel(period_content["MRI_triangle_number_of_sell"],
                    trans_MRI(u"sell")),
        get_pluriel(period_content["MRI_triangle_sum_of_sell"], pms.MONNAIE)
    )
    txt += u"<br />"
    txt += trans_MRI(u"On the star market, you've made {} ({}) and {} ({}).").format(
        get_pluriel(period_content["MRI_star_number_of_purchase"],
                    trans_MRI(u"purchase")),
        get_pluriel(period_content["MRI_star_sum_of_purchase"], pms.MONNAIE),
        get_pluriel(period_content["MRI_star_number_of_sell"],
                    trans_MRI(u"sell")),
        get_pluriel(period_content["MRI_star_sum_of_sell"], pms.MONNAIE)
    )
    txt += u"</br >"
    txt += trans_MRI(u"It's the {} event that has been drawn.").format(
        u"triangle" if period_content["MRI_event"] == pms.TRIANGLE else u"star")
    txt += u" "
    sells = period_content["MRI_triangle_number_of_sell"] if \
        period_content["MRI_event"] == pms.TRIANGLE else \
        period_content["MRI_star_number_of_sell"]
    purchases = period_content["MRI_triangle_number_of_purchase"] if \
        period_content["MRI_event"] == pms.TRIANGLE else \
        period_content["MRI_star_number_of_purchase"]
    txt += trans_MRI(u"You therefore have transfered {} and received {}.").format(
        get_pluriel(sells, pms.MONNAIE), get_pluriel(purchases, pms.MONNAIE))
    txt += u"<br />"
    txt += trans_MRI(u"Your payoff for this period is equal to {}").format(
        get_pluriel(period_content["MRI_periodpayoff"], pms.MONNAIE))
    logger.debug(txt)
    return txt


def get_event_str(event):
    return trans_MRI(u"Triangle") if event == pms.TRIANGLE else \
        trans_MRI(u"Star")


