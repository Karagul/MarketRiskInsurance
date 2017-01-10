# -*- coding: utf-8 -*-

import logging
import random

from twisted.internet import defer
from twisted.spread import pb
from client.cltremote import IRemote
from client.cltgui.cltguidialogs import GuiRecapitulatif
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceGui import GuiDecision
import MarketRiskInsuranceTexts as texts_MRI


logger = logging.getLogger("le2m")


class RemoteMRI(IRemote):
    """
    Class remote, remote_ methods can be called by the server
    """
    def __init__(self, le2mclt):
        IRemote.__init__(self, le2mclt)
        self._histo_vars = [
            "MRI_period", "MRI_decision",
            "MRI_periodpayoff", "MRI_cumulativepayoff"]
        self._histo.append(texts_MRI.get_histo_head())

    def remote_configure(self, params, server_part):
        """
        Set the same parameters as in the server side
        :param params:
        :return:
        """
        logger.info(u"{} configure".format(self._le2mclt.uid))
        for k, v in params.viewitems():
            setattr(pms, k, v)
        self._server_part = server_part

    def remote_newperiod(self, period):
        """
        Set the current period and delete the history
        :param period: the current period
        :return:
        """
        logger.info(u"{} Period {}".format(self._le2mclt.uid, period))
        self.currentperiod = period
        if self.currentperiod == 1:
            del self.histo[1:]

    def remote_display_decision(self):
        """
        Display the decision screen.
        No simulation mode
        :return: deferred
        """
        logger.info(u"{} Decision".format(self._le2mclt.uid))
        defered = defer.Deferred()
        self._decision_screen = GuiDecision(
            defered, self._le2mclt.automatique,
            self._le2mclt.screen, self.currentperiod, self.histo)
        self._decision_screen.show()
        return defered

    @defer.inlineCallbacks
    def send_offer(self, offer):
        rep = yield (self._server_part.add_proposition(offer))
        if not rep:
            self._decision_screen.display_offer_fail()

    def remote_display_summary(self, period_content):
        """
        Display the summary screen
        :param period_content: dictionary with the content of the current period
        :return: deferred
        """
        logger.info(u"{} Summary".format(self._le2mclt.uid))
        self.histo.append([period_content.get(k) for k in self._histo_vars])
        if self._le2mclt.simulation:
            return 1
        else:
            defered = defer.Deferred()
            ecran_recap = GuiRecapitulatif(
                defered, self._le2mclt.automatique, self._le2mclt.screen,
                self.currentperiod, self.histo,
                texts_MRI.get_text_summary(period_content))
            ecran_recap.show()
            return defered
