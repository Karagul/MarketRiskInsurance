# -*- coding: utf-8 -*-

import os
import logging
from collections import OrderedDict
from twisted.internet import defer
from random import randint, choice, shuffle
from util import utiltools
from util.utili18n import le2mtrans
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceGui import DConfigure, DWebView
from MarketRiskInsuranceTexts import trans_MRI
import pandas as pd
import datetime

logger = logging.getLogger("le2m.{}".format(__name__))


class Serveur(object):
    def __init__(self, le2mserv):
        self._le2mserv = le2mserv

        # creation of the menu (will be placed in the "part" menu on the
        # server screen)
        actions = OrderedDict()
        actions[trans_MRI(u"Help")] = self._display_help
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
            self._le2mserv.gestionnaire_graphique.infoserv(
                trans_MRI(u"treatment") + u": {}".format(
                pms.TREATMENTS_NAMES.get(pms.TREATMENT)))
            self._le2mserv.gestionnaire_graphique.infoserv(
                trans_MRI(u"Groups size") + u": {}".format(pms.TAILLE_GROUPES))
            self._le2mserv.gestionnaire_graphique.infoserv(
                trans_MRI(u"Number of periods") + u": {}".format(
                    pms.NOMBRE_PERIODES))
            self._le2mserv.gestionnaire_graphique.infoserv(
                trans_MRI(u"Amount to subtract to the cumulative payoff") +
                u": {}".format(pms.AMOUNT_TO_SUBTRACT))
            self._le2mserv.gestionnaire_graphique.infoserv(
                trans_MRI(u"Market duration") + u": {}".format(
                pms.MARKET_TIME))
            self._le2mserv.gestionnaire_graphique.infoserv(
                trans_MRI(u"Summary duration") + u": {}".format(
                    pms.SUMMARY_TIME))

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

            self._le2mserv.gestionnaire_graphique.infoserv(
                le2mtrans(u"Start time: {}".format(
                    datetime.datetime.now().strftime("%H:%M:%S"))))

            # random value and incomes
            random_value = randint(1, 100)
            period_event = pms.TRIANGLE if \
                random_value < (pms.PROB_TRIANGLE + 1) else \
                pms.STAR
            self._le2mserv.gestionnaire_graphique.infoserv(le2mtrans(
                u"Event") +u" : {}".format(
                u"Triangle" if period_event == pms.TRIANGLE else u"Star"))
            for g in self._le2mserv.gestionnaire_groupes.get_groupes().viewkeys():
                pms.INCOMES[g] = pms.get_incomes()
                if pms.TREATMENT != pms.P_2_FIX_6:
                    shuffle(pms.INCOMES[g])

            yield (self._le2mserv.gestionnaire_experience.run_func(
                self._tous, "newperiod", period, random_value))

            self._le2mserv.gestionnaire_graphique.infoserv(u"Incomes")
            for g in self._le2mserv.gestionnaire_groupes.get_groupes().viewkeys():
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"G{} {}".format(g.split("_")[2], pms.INCOMES[g]))
            
            # decision
            yield(self._le2mserv.gestionnaire_experience.run_step(
                le2mtrans(u"Decision"), self._tous, "display_decision"))
            
            # period payoffs
            self._le2mserv.gestionnaire_experience.compute_periodpayoffs(
                "MarketRiskInsurance")

            # for each group we collect all the transaction made during
            # the period
            self._le2mserv.gestionnaire_graphique.infoserv(u"Transactions")
            keys = ["MRI_trans_time", "MRI_trans_contract", "MRI_trans_buyer",
                    "MRI_trans_seller", "MRI_trans_price"]
            for g, m in self._le2mserv.gestionnaire_groupes.get_groupes(
                    "MarketRiskInsurance").viewitems():
                # a list with all the transactions in the group
                transactions_list = list()
                for j in m:
                    transactions_list.extend(j.get_transactions())
                logger.debug(u"transactions_list: {}".format(transactions_list))

                # we eliminate the duplicates
                transactions_set = [dict(t) for t in
                                    set([tuple(sorted(d.viewitems())) for d in
                                         transactions_list])]
                transactions_set.sort(key=lambda x: x["MRI_trans_time"])
                logger.debug(u"transactions_set: {}".format(transactions_set))

                # display on the server list
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"G{}".format(g.split("_")[2]))
                df_trans_group = pd.DataFrame(transactions_set)
                df_trans_group_contract_count = df_trans_group.groupby(
                    df_trans_group.MRI_trans_contract).count()
                df_trans_group_contract_mean = df_trans_group.groupby(
                    df_trans_group.MRI_trans_contract).mean()
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"Triangle: {} trans., av. price {:.2f}€".format(
                        df_trans_group_contract_count.loc[pms.TRIANGLE].MRI_trans_time,
                        df_trans_group_contract_mean.loc[pms.TRIANGLE].MRI_trans_price
                ))
                self._le2mserv.gestionnaire_graphique.infoserv(
                    u"Star: {} trans., av. price {:.2f}€".format(
                        df_trans_group_contract_count.loc[pms.STAR].MRI_trans_time,
                        df_trans_group_contract_mean.loc[pms.STAR].MRI_trans_price
                ))

                # self._le2mserv.gestionnaire_graphique.infoserv(
                #     [u"{MRI_trans_time}: {MRI_trans_contract}, "
                #      u"{MRI_trans_price}, {MRI_trans_buyer}, "
                #      u"{MRI_trans_seller}".format(**t) for t in
                #      transactions_set])

                # set the list of transactions in each player
                for j in m:
                    setattr(j, "_transactions_group", transactions_set)

            # summary
            yield(self._le2mserv.gestionnaire_experience.run_step(
                le2mtrans(u"Summary"), self._tous, "display_summary"))
        
        # End of part ==========================================================
        yield (self._le2mserv.gestionnaire_experience.finalize_part(
            "MarketRiskInsurance"))

    def _display_help(self):
        help_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "ReadMe.html"))
        logger.debug(u"Help file path: {}".format(help_file))
        self._screen = DWebView(help_file)
        self._screen.show()
