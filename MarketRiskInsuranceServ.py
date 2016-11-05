# -*- coding: utf-8 -*-

import logging
from collections import OrderedDict
from twisted.internet import defer
from random import randint
from util import utiltools
from util.utili18n import le2mtrans
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceGui import DConfigure


logger = logging.getLogger("le2m.{}".format(__name__))


class Serveur(object):
    def __init__(self, le2mserv):
        self._le2mserv = le2mserv

        # creation of the menu (will be placed in the "part" menu on the
        # server screen)
        actions = OrderedDict()
        actions[le2mtrans(u"Configure")] = self._configure
        actions[le2mtrans(u"Display parameters")] = \
            lambda _: self._le2mserv.gestionnaire_graphique. \
            display_information2(
                utiltools.get_module_info(pms), le2mtrans(u"Parameters"))
        actions[le2mtrans(u"Start")] = lambda _: self._demarrer()
        actions[le2mtrans(u"Display payoffs")] = \
            lambda _: self._le2mserv.gestionnaire_experience.\
            display_payoffs_onserver("MarketRiskInsurance")
        self._le2mserv.gestionnaire_graphique.add_topartmenu(
            u"Market Risk - Insurance", actions)

    def _configure(self):
        screen_conf = DConfigure(self._le2mserv.gestionnaire_graphique.screen)
        if screen_conf.exec_():
            self._le2mserv.gestionnaire_graphique.infoserv(u"Traitement: {}".format(
                pms.TREATMENTS_NAMES.get(pms.TREATMENT)))
            self._le2mserv.gestionnaire_graphique.infoserv(u"Période d'essai: {}".format(
                u"oui" if pms.PERIODE_ESSAI else u"non"))
            self._le2mserv.gestionnaire_graphique.infoserv(u"Durée du marché: {}".format(
                pms.TEMPS))

    @defer.inlineCallbacks
    def _demarrer(self):
        """
        Start the part
        :return:
        """
        # check conditions =====================================================
        if not self._le2mserv.gestionnaire_graphique.question(
                        le2mtrans(u"Start") + u" MarketRiskInsurance?"):
            return

        # init part ============================================================
        yield (self._le2mserv.gestionnaire_experience.init_part(
            "MarketRiskInsurance", "PartieMRI",
            "RemoteMRI", pms))
        self._tous = self._le2mserv.gestionnaire_joueurs.get_players(
            'MarketRiskInsurance')

        # set parameters on remotes
        yield (self._le2mserv.gestionnaire_experience.run_step(
            le2mtrans(u"Configure"), self._tous, "configure"))
        
        # form groups
        if pms.TAILLE_GROUPES > 0:
            try:
                self._le2mserv.gestionnaire_groupes.former_groupes(
                    self._le2mserv.gestionnaire_joueurs.get_players(),
                    pms.TAILLE_GROUPES, forcer_nouveaux=True)
            except ValueError as e:
                self._le2mserv.gestionnaire_graphique.display_error(
                    e.message)
                return
    
        # Start part ===========================================================
        for period in range(1 if pms.NOMBRE_PERIODES else 0,
                        pms.NOMBRE_PERIODES + 1):

            if self._le2mserv.gestionnaire_experience.stop_repetitions:
                break

            # init period
            self._le2mserv.gestionnaire_graphique.infoserv(
                [None, le2mtrans(u"Period") + u" {}".format(period)])
            self._le2mserv.gestionnaire_graphique.infoclt(
                [None, le2mtrans(u"Period") + u" {}".format(period)],
                fg="white", bg="gray")
            # tirage entier
            valeur_aleatoire = randint(1, 100)
            yield (self._le2mserv.gestionnaire_experience.run_func(
                self._tous, "newperiod", period, valeur_aleatoire))
            
            # decision
            yield(self._le2mserv.gestionnaire_experience.run_step(
                le2mtrans(u"Decision"), self._tous, "display_decision"))
            
            # period payoffs
            self._le2mserv.gestionnaire_experience.compute_periodpayoffs(
                "MarketRiskInsurance")
        
            # summary
            yield(self._le2mserv.gestionnaire_experience.run_step(
                le2mtrans(u"Summary"), self._tous, "display_summary"))
        
        # End of part ==========================================================
        yield (self._le2mserv.gestionnaire_experience.finalize_part(
            "MarketRiskInsurance"))
