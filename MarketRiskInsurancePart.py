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
        yield (self.remote.callRemote("configure", get_module_attributes(pms)))
        self.joueur.info(u"Ok")

    @defer.inlineCallbacks
    def newperiod(self, period, random_value):
        """
        Create a new period and inform the remote
        If this is the first period then empty the historic
        :param periode:
        :return:
        """
        logger.debug(u"{} New Period".format(self.joueur))
        self.currentperiod = RepetitionsMRI(period, random_value)
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


class RepetitionsMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    partie_partie_id = Column(
        Integer,
        ForeignKey("partie_MarketRiskInsurance.partie_id"))
    MRI_offers = relationship('OffersMRI')

    MRI_period = Column(Integer)
    MRI_treatment = Column(Integer)
    MRI_group = Column(Integer)
    MRI_random_value = Column(Integer)
    MRI_decision = Column(Integer)
    MRI_decisiontime = Column(Integer)
    MRI_periodpayoff = Column(Float)
    MRI_cumulativepayoff = Column(Float)

    def __init__(self, period, random_value):
        self.MRI_treatment = pms.TREATMENT
        self.MRI_period = period
        self.MRI_random_value = random_value
        self.MRI_decisiontime = 0
        self.MRI_periodpayoff = 0
        self.MRI_cumulativepayoff = 0

    def todict(self, joueur=None):
        temp = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if joueur:
            temp["joueur"] = joueur
        return temp

class OffersMRI(Base):
    __tablename__ = 'partie_MarketRiskInsurance_repetitions_offers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repetitions_id = Column(Integer,
                            ForeignKey("partie_MarketRiskInsurance_repetitions.id"))

    MRI_time = Column(String)
    MRI_sender = Column(String)
    MRI_sender_group = Column(String)
    MRI_type = Column(Integer)
    MRI_offer = Column(Float)

    def __init__(self, time, sender, sender_group, type, offer):
        self.MRI_time = time
        self.MRI_sender = sender
        self.MRI_sender_group = sender_group
        self.MRI_type = type
        self.MRI_offer = offer

    def todict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}