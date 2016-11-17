# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from twisted.internet import defer
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from server.servbase import Base
from server.servparties import Partie
from util.utiltools import get_module_attributes
import MarketRiskInsuranceParams as pms


logger = logging.getLogger("le2m")


class PartieMRI(Partie):
    __tablename__ = "partie_MarketRiskInsurance"
    __mapper_args__ = {'polymorphic_identity': 'MarketRiskInsurance'}
    partie_id = Column(Integer, ForeignKey('parties.id'), primary_key=True)
    repetitions = relationship('RepetitionsMRI')

    def __init__(self, le2mserv, joueur):
        super(PartieMRI, self).__init__(
            nom="MarketRiskInsurance", nom_court="MRI",
            joueur=joueur, le2mserv=le2mserv)
        self.MRI_gain_ecus = 0
        self.MRI_gain_euros = 0

    @defer.inlineCallbacks
    def configure(self):
        logger.debug(u"{} Configure".format(self.joueur))
        yield (self.remote.callRemote("configure", get_module_attributes(pms),
                                      self))
        self.joueur.info(u"Ok")

    @defer.inlineCallbacks
    def newperiod(self, period, random_value):
        """
        Create a new period and inform the remote
        :param period: the current period number
        :param the random value drawn by the server
        :return:
        """
        logger.debug(u"{} New Period".format(self.joueur))

        self.currentperiod = RepetitionsMRI(period)
        self.currentperiod.MRI_random_value = random_value
        self.currentperiod.MRI_group = self.joueur.group

        self.le2mserv.gestionnaire_base.ajouter(self.currentperiod)
        self.repetitions.append(self.currentperiod)

        yield (self.remote.callRemote("newperiod", period))
        logger.info(u"{} Ready for period {}".format(self.joueur, period))

    @defer.inlineCallbacks
    def display_decision(self):
        """
        Display the decision screen on the remote
        Get back the decision
        :return:
        """
        logger.debug(u"{} Decision".format(self.joueur))
        debut = datetime.now()
        self.currentperiod.MRI_decision = yield(self.remote.callRemote(
            "display_decision"))
        self.currentperiod.MRI_decisiontime = (datetime.now() - debut).seconds
        self.joueur.info(u"{}".format(self.currentperiod.MRI_decision))
        self.joueur.remove_waitmode()

    def compute_periodpayoff(self):
        """
        Compute the payoff for the period
        :return:
        """
        logger.debug(u"{} Period Payoff".format(self.joueur))
        self.currentperiod.MRI_periodpayoff = 0

        # cumulative payoff since the first period
        if self.currentperiod.MRI_period < 2:
            self.currentperiod.MRI_cumulativepayoff = \
                self.currentperiod.MRI_periodpayoff
        else: 
            previousperiod = self.periods[self.currentperiod.MRI_period - 1]
            self.currentperiod.MRI_cumulativepayoff = \
                previousperiod.MRI_cumulativepayoff + \
                self.currentperiod.MRI_periodpayoff

        # we store the period in the self.periodes dictionnary
        self.periods[self.currentperiod.MRI_period] = self.currentperiod

        logger.debug(u"{} Period Payoff {}".format(
            self.joueur,
            self.currentperiod.MRI_periodpayoff))

    @defer.inlineCallbacks
    def display_summary(self, *args):
        """
        Send a dictionary with the period content values to the remote.
        The remote creates the text and the history
        :param args:
        :return:
        """
        logger.debug(u"{} Summary".format(self.joueur))
        yield(self.remote.callRemote(
            "display_summary", self.currentperiod.todict()))
        self.joueur.info("Ok")
        self.joueur.remove_waitmode()

    @defer.inlineCallbacks
    def compute_partpayoff(self):
        """
        Compute the payoff for the part and set it on the remote.
        The remote stores it and creates the corresponding text for display
        (if asked)
        :return:
        """
        logger.debug(u"{} Part Payoff".format(self.joueur))

        self.MRI_gain_ecus = self.currentperiod.MRI_cumulativepayoff
        self.MRI_gain_euros = float(self.MRI_gain_ecus) * float(pms.TAUX_CONVERSION)
        yield (self.remote.callRemote(
            "set_payoffs", self.MRI_gain_euros, self.MRI_gain_ecus))

        logger.info(u'{} Payoff ecus {} Payoff euros {:.2f}'.format(
            self.joueur, self.MRI_gain_ecus, self.MRI_gain_euros))

    def remote_add_proposition(self, infos_prop):
        if self._is_prop_ok(infos_prop)[0]:
            pass
        else:
            pass

    def remote_remove_proposition(self, infos_prop):
        pass

    def _is_prop_ok(self, infos_prop):
        """"
        We check that the proposition is compatible with the player's budget
        in any event.
        1) check the player doesn't already have made a better proposition
        2) check the player can buy the proposition
        3) check the player's payoff at the end of the period taking into
        account the two possible events
        Return a tuple either of size 2 if the result is false
        (False and the explanation) or of size 1 if the result is true.
        """
        logger.debug(u"{}: test of prop: {}".format(self.joueur, infos_prop))

        # proposition's informations
        contract = infos_prop['contract']  # triangle or star
        kind = infos_prop["type"]  # purchase or sell
        price = infos_prop["price"]

        # Checks that the proposition is not less interesting than another one
        # proposed by the player himself
        prop_in_progress = [p for p in self.currentperiod.MRI_propositions if
                            p.MRI_prop_status == pms.IN_PROGRESS and
                            p.MRI_prop_contract == contract and
                            p.MRI_prop_type == kind]

        if kind == pms.BUY:
            best_props = [p for p in prop_in_progress if
                          p.MRI_prop_price > price]
        else:
            best_props = [p for p in prop_in_progress if
                          p.MRI_prop_price < price]

        if best_props:
            return (False, u"Vous avez une meilleure proposition en cours.")

        transactions_balance = self._get_transactions_balance()

        solde_achats_ventes = self._get_solde_achats_ventes()
        solde_recu_verse_triangle = self._get_solde_recu_verse(parametres.TRIANGLE)
        solde_recu_verse_star = self._get_solde_recu_verse(parametres.STAR)

        # check the player has a budget that corresponds to at least CAPITAL_REQUIREMENT of the price, without taking into account the events
        if type == parametres.ACHAT:
            if self.periodeCourante.revenu + solde_achats_ventes < Decimal(
                    str(prix)) * parametres.CAPITAL_REQUIREMENT:
                return (
                False, u"Vous n'avez pas le budget nécessaire pour cet achat.")

        # check the player has a budget that corresponds to at leat CAPITAL_REQUIREMENT of the price, if the event if TRIANGLE
        elif type == parametres.VENTE:
            if contrat == parametres.TRIANGLE:
                solde_recu_verse_triangle -= parametres.TRIANGLE_VERSEMENT
                if solde_recu_verse_triangle < 0:
                    if self.periodeCourante.revenu + solde_achats_ventes < Decimal(
                            str(abs(
                                    solde_recu_verse_triangle))) * parametres.CAPITAL_REQUIREMENT:
                        return (False,
                                u"Vous n'avez pas le budget nécessaire pour cette vente si l'évènement \"triangle\" se réalise.")
            elif contrat == parametres.STAR:
                solde_recu_verse_star -= parametres.STAR_VERSEMENT
                if solde_recu_verse_star < 0:
                    if self.periodeCourante.revenu + solde_achats_ventes < Decimal(
                            str(abs(
                                    solde_recu_verse_star))) * parametres.CAPITAL_REQUIREMENT:
                        return (False,
                                u"Vous n'avez pas le budget nécessaire pour cette vente si l'évènement \"étoile\" se réalise.")

        # si tous les tests sont passés
        logger.debug(u"Résultat du test: True")
        return (True,)

    def _get_transactions_balance(self):
        """
        Return the sum of the player's sells minus the sum of the player's
        purchases.
        """
        purchases = sum([t.MRI_trans_price for t in
                         self.currentperiod.MRI_transactions if
                         t.MRI_trans_buyer == self.joueur.uid])

        sells = sum([t.MRI_trans_price for t in
                         self.currentperiod.MRI_transactions if
                         t.MRI_trans_seller == self.joueur.uid])

        return sells - purchases


class RepetitionsMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    partie_partie_id = Column(
        Integer,
        ForeignKey("partie_MarketRiskInsurance.partie_id"))
    MRI_propositions = relationship('PropositionsMRI')
    MRI_transactions = relationship('TransactionsMRI')

    MRI_period = Column(Integer)
    MRI_treatment = Column(Integer)
    MRI_group = Column(Integer)
    MRI_random_value = Column(Integer)
    MRI_decision = Column(Integer)
    MRI_decisiontime = Column(Integer)
    MRI_periodpayoff = Column(Float)
    MRI_cumulativepayoff = Column(Float)

    def __init__(self, period):
        self.MRI_treatment = pms.TREATMENT
        self.MRI_period = period
        self.MRI_decisiontime = 0
        self.MRI_periodpayoff = 0
        self.MRI_cumulativepayoff = 0

    def todict(self, joueur=None):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if joueur:
            temp["joueur"] = joueur
        return temp


class PropositionsMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions_propositions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(
        Integer, ForeignKey("partie_MarketRiskInsurance_repetitions.id"))

    counter = 0

    MRI_prop_id = Column(Integer)
    MRI_prop_time = Column(String)
    MRI_prop_sender = Column(String)
    MRI_prop_contract = Column(Integer)
    MRI_prop_type = Column(Integer)
    MRI_prop_price = Column(Float)
    MRI_prop_status = Column(Integer)

    def __init__(self, prop_infos):

        self.MRI_prop_id = PropositionsMRI.counter
        self.MRI_prop_time = prop_infos.get("time")
        self.MRI_prop_sender = prop_infos.get("sender")
        self.MRI_prop_type = prop_infos.get("type")
        self.MRI_prop_price = prop_infos.get("price")

        PropositionsMRI.counter += 1

    def todict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TransactionsMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(
        Integer, ForeignKey("partie_MarketRiskInsurance_repetitions.id"))

    MRI_trans_time = Column(String)
    MRI_trans_buyer = Column(String)
    MRI_trans_seller = Column(String)
    MRI_trans_contract = Column(Integer)
    MRI_trans_price = Column(Float)

    def __init__(self, time, buyer, seller, contract, price):

        self.MRI_trans_time = time
        self.MRI_trans_buyer = buyer
        self.MRI_trans_seller = seller
        self.MRI_trans_contract = contract
        self.MRI_trans_price = price

    def todict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}