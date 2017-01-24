select distinct s.nom as session, j.uid as joueur, rep.*, trans.* from partie_marketriskinsurance_repetitions_transactions trans, partie_marketriskinsurance_repetitions rep, partie_marketriskinsurance part,
joueurs j, parties_joueurs__joueurs_parties pj, sessions s, parties p
where s.isTest=0
and j.session_id = s.id
and pj.joueurs_uid = j.uid
and p.id = pj.parties_id
and rep.partie_partie_id = p.id
and trans.repetitions_id = rep.id
