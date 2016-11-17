# -*- coding: utf-8 -*-
"""
This module contains the GUI
"""

import logging
from PyQt4 import QtGui, QtCore
from util.utili18n import le2mtrans
import MarketRiskInsuranceParams as pms
from MarketRiskInsuranceTexts import trans_MRI
import MarketRiskInsuranceTexts as texts_MRI
from client.cltgui.cltguidialogs import GuiHistorique
from client.cltgui.cltguiwidgets import WPeriod, WExplication, WSpinbox


logger = logging.getLogger("le2m")


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
    def __init__(self, defered, automatique, parent, period, historique):
        super(GuiDecision, self).__init__(parent)

        # variables
        self._defered = defered
        self._automatique = automatique
        self._historique = GuiHistorique(self, historique)

        layout = QtGui.QVBoxLayout(self)

        # should be removed if one-shot game
        wperiod = WPeriod(
            period=period, ecran_historique=self._historique)
        layout.addWidget(wperiod)

        wexplanation = WExplication(
            text=texts_MRI.get_text_explanation(),
            size=(450, 80), parent=self)
        layout.addWidget(wexplanation)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)

        # left part; triangle
        left_layout = QtGui.QVBoxLayout()
        hlayout.addLayout(left_layout)
        self._triangle_achat = MyTree()
        self._triangle_vente = MyTree()
        left_layout.addWidget(self._triangle_achat)
        left_layout.addWidget(self._triangle_vente)

        # right part: star
        right_layout = QtGui.QVBoxLayout()
        hlayout.addLayout(right_layout)
        self._star_achat = MyTree()
        self._star_vente = MyTree()
        right_layout.addWidget(self._star_achat)
        right_layout.addWidget(self._star_vente)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

        self.setWindowTitle(trans_MRI(u"Title"))
        self.adjustSize()
        self.setFixedSize(self.size())

        if self._automatique:
            self._timer_automatique = QtCore.QTimer()
            self._timer_automatique.timeout.connect(
                buttons.button(QtGui.QDialogButtonBox.Ok).click)
            self._timer_automatique.start(7000)
                
    def reject(self):
        pass
    
    def _accept(self):
        try:
            self._timer_automatique.stop()
        except AttributeError:
            pass
        decision = self._wdecision.get_value()
        if not self._automatique:
            confirmation = QtGui.QMessageBox.question(
                self, le2mtrans(u"Confirmation"),
                le2mtrans(u"Do you confirm your choice?"),
                QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            if confirmation != QtGui.QMessageBox.Yes: 
                return
        logger.info(u"Send back {}".format(decision))
        self.accept()
        self._defered.callback(decision)


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
        self._timeEdit.setTime(QtCore.QTime(pms.TEMPS.hour,
                                            pms.TEMPS.minute,
                                            pms.TEMPS.second))
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
        pms.TEMPS = self._timeEdit.time().toPyTime()
        pms.NOMBRE_PERIODES = self._spin_periods.value()
        pms.TAILLE_GROUPES = self._spin_groups.value()
        self.accept()
