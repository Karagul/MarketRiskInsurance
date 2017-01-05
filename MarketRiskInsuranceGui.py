# -*- coding: utf-8 -*-
"""
This module contains the GUI
"""

import sys
import logging
from PyQt4 import QtGui, QtCore
from twisted.internet import defer
from random import randint, choice
# from util.utili18n import le2mtrans
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceTexts import trans_MRI
import MarketRiskInsuranceTexts as texts_MRI
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguiwidgets import WPeriod, WExplication, WSpinbox, WCompterebours


logger = logging.getLogger("le2m")


class MyStandardItem(QtGui.QStandardItem):
    """
    Surcharge du standard item pour la fonction sort de la liste qui
    accueillera ces items
    """
    def __init__(self, value):
        QtGui.QStandardItem.__init__(self)
        self.__value = value
        self.setText(str(value))

    def __lt__(self, other):
        return other < self.__value

    def value(self):
        return self.__value


class MyTree(QtGui.QTreeWidget):
    def __init__(self):
        QtGui.QTreeWidget.__init__(self)
        self.setHeaderItem(QtGui.QTreeWidgetItem(
            [u"ID", u"Type", u"Prix", u"Quantité"]))
        # self.header().setCascadingSectionResizes(True)
        # self.header().setDefaultSectionSize(30)
        # self.header().setMinimumSectionSize(30)
        # self.header().setStretchLastSection(False)
        self.header().setResizeMode(QtGui.QHeaderView.Stretch)
        self.setFixedWidth(350)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def addItem(self, list_of_elements):
        self.addTopLevelItem(map(str, list_of_elements))


class GuiDecision(QtGui.QDialog):
    def __init__(self, defered, automatique, parent, period, historique, remote):
        super(GuiDecision, self).__init__(parent)

        # variables
        self._defered = defered
        self._automatique = automatique
        self._historique = GuiHistorique(self, historique)
        self._remote = remote

        layout = QtGui.QVBoxLayout(self)

        wperiod = WPeriod(
            period=period, ecran_historique=self._historique)
        layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_MRI.get_text_explanation(),
            size=(450, 80), parent=self)
        layout.addWidget(wexplanation)

        # Compte à rebours
        self._compte_rebours = WCompterebours(
            parent=self, temps=pms.MARKET_TIME, actionfin=self._accept)
        layout.addWidget(self._compte_rebours)

        # market
        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)

        # left part: triangle ==================================================
        triangle_layout = QtGui.QGridLayout()
        hlayout.addLayout(triangle_layout)
        triangle_layout_line = 0

        triangle_layout.addWidget(QtGui.QLabel(trans_MRI(u"Purchase offers")),
                                  triangle_layout_line, 0)
        triangle_layout.addWidget(QtGui.QLabel(trans_MRI(u"Sell offers")),
                                  triangle_layout_line, 1)

        triangle_layout_line += 1

        # --- lists
        # purchase
        self._triangle_purchase_model = QtGui.QStandardItemModel()
        self._triangle_purchase__listview = QtGui.QListView()
        self._triangle_purchase__listview.setModel(self._triangle_purchase_model)
        self._triangle_purchase__listview.setMaximumSize(300, 600)
        triangle_layout.addWidget(self._triangle_purchase__listview,
                                       triangle_layout_line, 0)

        # sell
        self._triangle_sell_model = QtGui.QStandardItemModel()
        self._triangle_sell_listview = QtGui.QListView()
        self._triangle_sell_listview.setModel(self._triangle_sell_model)
        self._triangle_sell_listview.setMaximumSize(300, 600)
        triangle_layout.addWidget(self._triangle_sell_listview,
                                       triangle_layout_line, 1)

        triangle_layout_line += 1

        # --- offers' zone
        # purchase
        self._triangle_purchase_offer_layout = QtGui.QHBoxLayout()
        self._triangle_purchase_offer_layout.addWidget(
            QtGui.QLabel(trans_MRI(u"Purchase offer")))
        self._triangle_purchase_spin_offer = QtGui.QDoubleSpinBox()
        self._triangle_purchase_spin_offer.setDecimals(pms.DECIMALS)
        self._triangle_purchase_spin_offer.setMinimum(0)
        self._triangle_purchase_spin_offer.setMaximum(pms.OFFER_MAX)
        self._triangle_purchase_spin_offer.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._triangle_purchase_spin_offer.setMaximumWidth(50)
        self._triangle_purchase_offer_layout.addWidget(
            self._triangle_purchase_spin_offer)
        self._triangle_purchase_button_send_offer = QtGui.QPushButton(
            trans_MRI(u"Send"))
        self._triangle_purchase_button_send_offer.setMaximumWidth(100)
        self._triangle_purchase_button_send_offer.clicked.connect(
            lambda _: self._send_offer(
                pms.TRIANGLE, pms.BUY, self._triangle_purchase_spin_offer.value()))
        self._triangle_purchase_offer_layout.addWidget(
            self._triangle_purchase_button_send_offer)
        self._triangle_purchase_offer_layout.addSpacerItem(
            QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Minimum))
        triangle_layout.addLayout(self._triangle_purchase_offer_layout,
                                  triangle_layout_line, 0)

        # sell
        self._triangle_sell_offer_layout = QtGui.QHBoxLayout()
        self._triangle_sell_offer_layout.addWidget(
            QtGui.QLabel(trans_MRI(u"Sell offer")))
        self._triangle_sell_spin_offer = QtGui.QDoubleSpinBox()
        self._triangle_sell_spin_offer.setDecimals(pms.DECIMALS)
        self._triangle_sell_spin_offer.setMinimum(0)
        self._triangle_sell_spin_offer.setMaximum(pms.OFFER_MAX)
        self._triangle_sell_spin_offer.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._triangle_sell_spin_offer.setMaximumWidth(50)
        self._triangle_sell_offer_layout.addWidget(self._triangle_sell_spin_offer)
        self._triangle_sell_button_send_offer = QtGui.QPushButton(
            trans_MRI(u"Send"))
        self._triangle_sell_button_send_offer.setMaximumWidth(100)
        self._triangle_sell_button_send_offer.clicked.connect(
            lambda _: self._remote_send_offer(
                pms.TRIANGLE, pms.SELL, self._triangle_sell_spin_offer.value()))
        self._triangle_sell_offer_layout.addWidget(
            self._triangle_sell_button_send_offer)
        self._triangle_sell_offer_layout.addSpacerItem(
            QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Expanding,
                              QtGui.QSizePolicy.Minimum))
        triangle_layout.addLayout(self._triangle_sell_offer_layout,
                                  triangle_layout_line, 0)


        self.setWindowTitle(trans_MRI(u"Market"))
        self.adjustSize()
        self.setFixedSize(self.size())

        if self._automatique:
            self._timer_automatique = QtCore.QTimer()
            self._timer_automatique.timeout.connect(self._play_auto)
            self._timer_automatique.start(7000)
                
    def reject(self):
        pass
    
    def _accept(self):
        try:
            self._timer_automatique.stop()
        except AttributeError:
            pass
        logger.info(u"Ok")
        self.accept()
        self._defered.callback(True)

    @defer.inlineCallbacks
    def _send_offer(self, triangle_or_star, buy_or_sell, value):
        logger.debug("call of send_offer")
        offer = {"MRI_prop_contract": triangle_or_star,
                 "MRI_prop_type": buy_or_sell,
                 "MRI_prop_price": value}
        yield (self._remote.send_offer(offer))

    def display_offer_failure(self):
        QtGui.QMessageBox.warning(
            self, trans_MRI(u"Be careful"),
            trans_MRI(u"You can't do this offer"))
        return

    def _play_auto(self):
        """
        called by the timer when the program play automatically
        :return:
        """
        # make an offer
        triangle_or_star = choice([pms.TRIANGLE, pms.STAR])
        buy_or_sell = choice([pms.BUY, pms.SELL])
        value = randint(0, pms.OFFER_MAX)




class DConfigure(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        form = QtGui.QFormLayout()
        layout.addLayout(form)

        # treatment
        self._combo_treatment = QtGui.QComboBox()
        self._combo_treatment.addItems(
            list(sorted(pms.TREATMENTS_NAMES.viewvalues())))
        self._combo_treatment.setCurrentIndex(pms.TREATMENT)
        form.addRow(QtGui.QLabel(u"Traitement"), self._combo_treatment)

        # nombre de périodes
        self._spin_periods = QtGui.QSpinBox()
        self._spin_periods.setMinimum(0)
        self._spin_periods.setMaximum(100)
        self._spin_periods.setSingleStep(1)
        self._spin_periods.setValue(pms.NOMBRE_PERIODES)
        self._spin_periods.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_periods.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Nombre de périodes"), self._spin_periods)

        # periode essai
        self._checkbox_essai = QtGui.QCheckBox()
        self._checkbox_essai.setChecked(pms.PERIODE_ESSAI)
        form.addRow(QtGui.QLabel(u"Période d'essai"), self._checkbox_essai)

        # taille groupes
        self._spin_groups = QtGui.QSpinBox()
        self._spin_groups.setMinimum(2)
        self._spin_groups.setMaximum(100)
        self._spin_groups.setSingleStep(1)
        self._spin_groups.setValue(pms.TAILLE_GROUPES)
        self._spin_groups.setButtonSymbols(QtGui.QSpinBox.NoButtons)
        self._spin_groups.setMaximumWidth(50)
        form.addRow(QtGui.QLabel(u"Taille des groupes"), self._spin_groups)

        # temps de marché
        self._timeEdit = QtGui.QTimeEdit()
        self._timeEdit.setDisplayFormat("hh:mm:ss")
        self._timeEdit.setTime(QtCore.QTime(pms.MARKET_TIME.hour,
                                            pms.MARKET_TIME.minute,
                                            pms.MARKET_TIME.second))
        self._timeEdit.setMaximumWidth(100)
        form.addRow(QtGui.QLabel(u"Durée du marché"), self._timeEdit)

        button = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        button.accepted.connect(self._accept)
        button.rejected.connect(self.reject)
        layout.addWidget(button)

        self.setWindowTitle(u"Configurer")
        self.adjustSize()
        self.setFixedSize(self.size())

    def _accept(self):
        pms.TREATMENT = self._combo_treatment.currentIndex()
        pms.PERIODE_ESSAI = self._checkbox_essai.isChecked()
        pms.MARKET_TIME = self._timeEdit.time().toPyTime()
        pms.NOMBRE_PERIODES = self._spin_periods.value()
        pms.TAILLE_GROUPES = self._spin_groups.value()
        self.accept()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    my_screen = GuiDecision(
        defered=None,
        automatique=False,
        parent=None,
        period=1,
        historique=None,
        remote=None
    )
    my_screen.show()
    sys.exit(app.exec_())
