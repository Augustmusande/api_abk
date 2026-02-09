# 📊 ENDPOINTS DE CALCULS - DOCUMENTATION COMPLÈTE

## 📁 APPLICATION CAISSE (`/api/caisse/`)

### 1. **CalculsFinanciersViewSet** (`/api/caisse/calculs/`)

#### 1.1. **GET `/api/caisse/calculs/interets/`**
**Fonction :** `calculer_interets_tous_credits()` dans `caisse/services.py`
- **Description :** Calcule les intérêts de tous les crédits
- **Formule :** `interet = (montant * taux_interet) / 100`
- **Permissions :**
  - ADMIN/SUPERADMIN : Voit tous les intérêts
  - MEMBRE : Voit uniquement ses propres intérêts
  - CLIENT : Voit uniquement ses propres intérêts
- **Retourne :**
  - `interets_par_credit` : Liste des intérêts par crédit
  - `interets_par_membre` : Liste des intérêts par membre (pour ADMIN/SUPERADMIN)
  - `interet_total_global` : Intérêt total global
  - `nombre_credits` : Nombre de crédits

---

#### 1.2. **GET `/api/caisse/calculs/frais_gestion/?pourcentage=20`**
**Fonction :** `calculer_frais_gestion(pourcentage=20)` dans `caisse/services.py`
- **Description :** Calcule les frais de gestion sur l'intérêt total global
- **Formule :** `frais_gestion = (interet_total_global * pourcentage) / 100`
- **Paramètres :**
  - `pourcentage` (float, optionnel) : Pourcentage des frais de gestion (défaut: 20%)
- **Permissions :**
  - ADMIN/SUPERADMIN : Voit tous les frais de gestion
  - MEMBRE : Voit uniquement ses propres frais de gestion
  - CLIENT : Pas d'accès
- **Actions :** Crée automatiquement une transaction `ENTREE_APRES_CALCUL_FRAIS_GESTION`
- **Retourne :**
  - `pourcentage_utilise` : Pourcentage utilisé
  - `interet_total_global` : Intérêt total global
  - `frais_gestion_total_global` : Frais de gestion total
  - `frais_par_membre` : Liste des frais par membre (répartis proportionnellement)
  - `nombre_credits` : Nombre de crédits
  - `transaction_created` : True si transaction créée
  - `transaction_numTrans` : Numéro de transaction créée

---

#### 1.3. **GET `/api/caisse/calculs/resume/?pourcentage_frais_gestion=20`**
**Fonction :** Combine `calculer_interets_tous_credits()` et `calculer_frais_gestion()`
- **Description :** Retourne un résumé complet des calculs financiers
- **Paramètres :**
  - `pourcentage_frais_gestion` (float, optionnel) : Pourcentage des frais de gestion (défaut: 20)
  - `periode_mois` (int, optionnel) : Mois pour filtrer
  - `periode_annee` (int, optionnel) : Année pour filtrer
- **Permissions :** ADMIN/SUPERADMIN uniquement
- **Retourne :**
  - `interets` : Résultats des calculs d'intérêts
  - `frais_gestion` : Résultats des calculs de frais de gestion
  - `interet_net_a_repartir` : Intérêt net à répartir (intérêt total - frais de gestion)
  - `pourcentage_frais_gestion_utilise` : Pourcentage utilisé

---

#### 1.4. **GET `/api/caisse/calculs/apports_membres/?periode_mois=12&periode_annee=2025`**
**Fonction :** `calculer_apports_tous_membres(periode_mois, periode_annee)` dans `caisse/services.py`
- **Description :** Calcule les apports des membres (parts sociales + épargnes bloquées + comptes en vue)
- **Paramètres :**
  - `periode_mois` (int, optionnel) : Mois pour filtrer (1-12)
  - `periode_annee` (int, optionnel) : Année pour filtrer
- **Permissions :**
  - ADMIN/SUPERADMIN : Voit les apports de tous les membres
  - MEMBRE : Voit uniquement ses propres apports
  - CLIENT : Pas d'accès
- **Retourne :**
  - `apports_par_membre` : Liste des apports par membre
  - `total_parts_sociales` : Total des parts sociales
  - `total_epargnes_bloquees` : Total des épargnes bloquées
  - `total_comptes_vue` : Total des comptes en vue
  - `total_credits_actifs` : Total des crédits actifs
  - `total_apports_global` : Total des apports globaux (apports bruts - crédits actifs)
  - `periode_mois` : Mois de la période
  - `periode_annee` : Année de la période

---

#### 1.5. **GET `/api/caisse/calculs/repartition_interets/?pourcentage_frais_gestion=20&periode_mois=12&periode_annee=2025`**
**Fonction :** `repartir_interets_aux_membres(pourcentage_frais_gestion, periode_mois, periode_annee)` dans `caisse/services.py`
- **Description :** Répartit les intérêts aux membres selon leurs apports
- **Formule :**
  - `proportion = (PartSocial_membre + epargne_bloquee_membre) / (PartSocialTotal + epargne_bloqueeTotal)`
  - `interet_membre = interet_net_a_repartir * proportion`
  - `interet_net_a_repartir = interet_total_global - frais_gestion_total_global`
- **Paramètres :**
  - `pourcentage_frais_gestion` (float, optionnel) : Pourcentage des frais de gestion (défaut: 20)
  - `periode_mois` (int, optionnel) : Mois pour filtrer les apports (1-12). Si None mais `periode_annee` spécifié, calcule le total annuel
  - `periode_annee` (int, optionnel) : Année pour filtrer les apports. Si non spécifiée, utilise l'année courante
- **Permissions :**
  - ADMIN/SUPERADMIN : Voit la répartition pour tous les membres
  - MEMBRE : Voit uniquement sa propre répartition
  - CLIENT : Pas d'accès
- **Retourne :**
  - `periode_mois` : Mois de la période (None si total annuel)
  - `periode_annee` : Année de la période
  - `interet_total_global` : Intérêt total global
  - `frais_gestion_total_global` : Frais de gestion total global
  - `interet_net_a_repartir` : Intérêt net à répartir
  - `total_parts_sociales` : Total des parts sociales
  - `total_epargnes_bloquees` : Total des épargnes bloquées
  - `total_comptes_vue` : Total des comptes en vue
  - `total_apports_global` : Total des apports globaux
  - `repartitions` : Liste des répartitions par membre (proportion et intérêt attribué)
  - `pourcentage_frais_gestion_utilise` : Pourcentage utilisé

---

### 2. **DepensesViewSet** (`/api/caisse/depenses/`)

#### 2.1. **GET `/api/caisse/depenses/total/`**
**Fonction :** Calcul direct dans la vue
- **Description :** Calcule le total des dépenses
- **Permissions :** ADMIN/SUPERADMIN uniquement
- **Retourne :**
  - `total_depenses` : Total des dépenses (somme de tous les `pt` des dépenses)
  - `nombre_depenses` : Nombre de dépenses

---

### 3. **TransactionViewSet** (`/api/caisse/transactions/`)

#### 3.1. **GET `/api/caisse/transactions/situation_caisse/`**
**Fonction :** Calcul direct dans la vue
- **Description :** Calcule la situation de la caisse générale
- **Formule :** `(ENTREE(TOTAL) + ENTREE_APRES_CALCUL_FRAIS_GESTION) - SORTIE(TOTAL)`
- **Permissions :** ADMIN/SUPERADMIN uniquement
- **Retourne :**
  - `total_entrees` : Total des entrées (type ENTREE)
  - `total_frais_gestion` : Total des frais de gestion (type ENTREE_APRES_CALCUL_FRAIS_GESTION)
  - `total_sorties` : Total des sorties (type SORTIE)
  - `solde_caisse` : Solde de la caisse (situation générale)
  - `nombre_entrees` : Nombre d'entrées
  - `nombre_frais_gestion` : Nombre de transactions de frais de gestion
  - `nombre_sorties` : Nombre de sorties
  - `formule` : Formule utilisée

---

### 4. **CaisseTypeViewSet** (`/api/caisse/caissetypes/`)

#### 4.1. **GET `/api/caisse/caissetypes/calculer_totaux/?date_debut=2025-01-01&date_fin=2025-12-31`**
**Fonction :** Calcul direct dans la vue
- **Description :** Calcule les totaux des montants par type de caisse
- **Paramètres :**
  - `date_debut` (date, optionnel) : Date de début pour le filtrage (format: YYYY-MM-DD)
  - `date_fin` (date, optionnel) : Date de fin pour le filtrage (format: YYYY-MM-DD)
- **Permissions :** ADMIN/SUPERADMIN uniquement
- **Logique de calcul :**
  - **Transactions ENTREE** : Additionne le montant
  - **Transactions ENTREE_APRES_CALCUL_FRAIS_GESTION** : Additionne le montant
  - **Transactions SORTIE** : Soustrait le montant
  - **Remboursements** : Additionne le montant
  - **Donations d'épargne** : Additionne le montant
  - **Donations de part sociale** : Additionne le montant
  - **Frais d'adhésion** : Additionne le montant
  - **Dépenses** : Soustrait le montant (prix total `pt`)
  - **Retraits** : Soustrait le montant
- **Retourne :**
  - `count` : Nombre de types de caisse
  - `total_general` : Total général (différence entre toutes les entrées et sorties)
  - `total_general_entrees` : Total général des entrées
  - `total_general_sorties` : Total général des sorties
  - `results` : Liste des types de caisse avec :
    - `id` : ID du type de caisse
    - `nom` : Nom du type de caisse
    - `description` : Description
    - `image_url` : URL de l'image
    - `total_montant` : Total du montant (entrées - sorties)
    - `total_entrees` : Total des entrées
    - `total_sorties` : Total des sorties
    - `nombre_mouvements` : Nombre de mouvements
    - `last_updated` : Date de dernière mise à jour
    - `created_at` : Date de création

---

### 5. **CaissetypemvtViewSet** (`/api/caisse/caissetypemvt/`)

#### 5.1. **GET `/api/caisse/caissetypemvt/historique/?caissetype=1&date_debut=2025-01-01&date_fin=2025-12-31`**
**Fonction :** Calcul direct dans la vue
- **Description :** Retourne l'historique détaillé des opérations par type de caisse
- **Paramètres :**
  - `caissetype` (int, obligatoire) : ID du type de caisse
  - `date_debut` (date, optionnel) : Date de début (format: YYYY-MM-DD)
  - `date_fin` (date, optionnel) : Date de fin (format: YYYY-MM-DD)
- **Permissions :** ADMIN/SUPERADMIN uniquement
- **Retourne :**
  - `caissetype_id` : ID du type de caisse
  - `caissetype_nom` : Nom du type de caisse
  - `count` : Nombre d'opérations
  - `results` : Liste des opérations avec :
    - `id` : ID du mouvement
    - `date` : Date de l'opération
    - `type_operation` : Type d'opération (Transaction, Remboursement, Don d'épargne, etc.)
    - `sous_type` : Sous-type (ENTREE, SORTIE)
    - `montant` : Montant de l'opération
    - `libelle` : Libellé de l'opération
    - `transaction_id`, `remboursement_id`, `donnatepargne_id`, etc. : IDs des objets liés

---

## 📁 APPLICATION CREDITS (`/api/credits/`)

### 6. **Calculs dans les Serializers**

#### 6.1. **Validation lors de la création d'un crédit**
**Fonction :** `calculer_solde_caissetype_disponible(caissetype)` dans `caisse/services.py`
- **Description :** Calcule le solde disponible dans un type de caisse spécifique pour valider l'octroi d'un crédit
- **Formule :** `Solde = Donations + Entrées (hors crédits) - Sorties (hors dépenses) - Crédits actifs`
- **Utilisé dans :** `CreditSerializer.validate()` dans `credits/serializers.py`
- **Vérifie :**
  - Le solde disponible du `CaisseType` sélectionné
  - Un seuil minimum de 1 USD
  - Exclut les frais de gestion (réservés pour les dépenses)

---

#### 6.2. **Calcul du solde restant lors d'un remboursement**
**Fonction :** `Remboursement.save()` dans `credits/models.py`
- **Description :** Calcule le solde restant après un remboursement
- **Logique :**
  - Pour `PRECOMPTE` : `solde_restant` est initialisé à `montant` (total du crédit)
  - Pour `POSTCOMPTE` : `solde_restant` est initialisé à `montant - interet`
  - À chaque remboursement : `solde_restant = solde_restant - montant_remboursement`
- **Utilisé dans :** `RemboursementSerializer.validate()` dans `credits/serializers.py`

---

## 📁 APPLICATION MEMBRES (`/api/`)

### 7. **RetraitViewSet** (`/api/retraits/`)

#### 7.1. **Validation lors de la création d'un retrait**
**Fonction :** `calculer_solde_caissetype_disponible(caissetype)` dans `caisse/services.py`
- **Description :** Calcule le solde disponible dans un type de caisse spécifique pour valider un retrait
- **Utilisé dans :** `RetraitSerializer.validate()` dans `membres/serializers.py`
- **Vérifie :**
  - Le solde disponible du `CaisseType` sélectionné
  - Un seuil minimum de 1 USD
  - Exclut les frais de gestion

---

## 📁 APPLICATION RAPPORTS (`/api/`)

### 8. **RapportViewSet** (`/api/rapports/`)

#### 8.1. **POST `/api/rapports/generer/`**
**Fonction :** Diverses fonctions dans `rapports/services.py`
- **Description :** Génère différents types de rapports avec calculs
- **Types de rapports :**
  - `APPORTS` : Utilise `generer_rapport_apports()` → `calculer_apports_tous_membres()`
  - `INTERETS` : Utilise `generer_rapport_interets()` → `calculer_interets_tous_credits()` et `calculer_frais_gestion()`
  - `CAISSE` : Utilise `generer_rapport_caisse()` → Calculs de situation de caisse
  - `CREDITS` : Utilise `generer_rapport_credits()`
  - `TRANSACTIONS` : Utilise `generer_rapport_transactions()`
  - `MENSUEL` : Utilise `generer_rapport_mensuel()` → Combine plusieurs calculs
  - `ANNUEL` : Utilise `generer_rapport_annuel()` → Combine plusieurs calculs
- **Paramètres :**
  - `type_rapport` (string, obligatoire) : Type de rapport à générer
  - `periode_mois` (int, optionnel) : Mois pour filtrer
  - `periode_annee` (int, optionnel) : Année pour filtrer
  - `pourcentage_frais_gestion` (float, optionnel) : Pourcentage des frais de gestion (pour INTERETS)
  - `type_transaction` (string, optionnel) : Type de transaction (pour TRANSACTIONS)
  - `sauvegarder` (bool, optionnel) : Sauvegarder le rapport (défaut: True)
  - `envoyer_email` (bool, optionnel) : Envoyer par email (défaut: False)
  - `destinataire_email` (string, optionnel) : Email du destinataire

---

## 📁 FONCTIONS DE SERVICE PRINCIPALES

### 9. **Fonctions dans `caisse/services.py`**

#### 9.1. **`calculer_interet_credit(credit)`**
- **Formule :** `interet = (montant * taux_interet) / 100`
- **Utilisée par :** `calculer_interets_tous_credits()`

#### 9.2. **`calculer_interets_tous_credits()`**
- **Description :** Calcule les intérêts de tous les crédits
- **Retourne :** Dictionnaire avec intérêts par crédit, par membre, et total global

#### 9.3. **`calculer_frais_gestion(pourcentage=20)`**
- **Formule :** `frais_gestion = (interet_total_global * pourcentage) / 100`
- **Actions :** Crée automatiquement une transaction `ENTREE_APRES_CALCUL_FRAIS_GESTION`
- **Retourne :** Dictionnaire avec frais de gestion total et par membre

#### 9.4. **`calculer_solde_caissetype_disponible(caissetype)`**
- **Formule :** `Solde = Donations + Entrées (hors crédits) - Sorties (hors dépenses) - Crédits actifs`
- **Utilisée pour :** Validation des crédits et retraits
- **Exclut :** Frais de gestion (réservés pour les dépenses)

#### 9.5. **`calculer_apports_membre(membre, periode_mois=None, periode_annee=None)`**
- **Description :** Calcule les apports d'un membre (parts sociales + épargnes bloquées + comptes en vue)
- **Retourne :** Dictionnaire avec apports détaillés et totaux

#### 9.6. **`calculer_apports_tous_membres(periode_mois=None, periode_annee=None)`**
- **Description :** Calcule les apports de tous les membres
- **Retourne :** Dictionnaire avec apports par membre et totaux globaux

#### 9.7. **`repartir_interets_aux_membres(pourcentage_frais_gestion=20, periode_mois=None, periode_annee=None)`**
- **Formule :**
  - `proportion = apports_membre / total_apports_global`
  - `interet_membre = interet_net_a_repartir * proportion`
- **Retourne :** Dictionnaire avec répartition complète par membre

---

## 📁 CALCULS DANS LES MODÈLES

### 10. **Calculs automatiques dans `credits/models.py`**

#### 10.1. **`Credit.save()`**
- **Calculs automatiques :**
  - `interet` : `(montant * taux_interet) / 100`
  - `montant_effectif` : `montant - interet` (pour PRECOMPTE) ou `montant` (pour POSTCOMPTE)
  - `solde_restant` : `montant` (pour PRECOMPTE) ou `montant - interet` (pour POSTCOMPTE)
  - `date_fin` : Calculée selon `duree` et `duree_type`

#### 10.2. **`Remboursement.save()`**
- **Calculs automatiques :**
  - `solde_restant` : Mis à jour après chaque remboursement
  - `score` : Calculé selon la date de remboursement (bonus/malus)
  - `statut` du crédit : Mis à jour automatiquement (EN_COURS, TERMINE, etc.)

---

## 📁 CALCULS DANS LES SERIALIZERS

### 11. **Calculs de validation dans `caisse/serializers.py`**

#### 11.1. **`DepensesSerializer._calculer_solde_caisse()`**
- **Formule :** `(ENTREE(TOTAL) + ENTREE_APRES_CALCUL_FRAIS_GESTION) - SORTIE(TOTAL)`
- **Utilisé pour :** Validation des dépenses (qui peuvent utiliser les frais de gestion)

#### 11.2. **`DepensesSerializer._calculer_solde_caisse_sans_frais_gestion()`**
- **Formule :** `ENTREE(TOTAL) - SORTIE(TOTAL)`
- **Utilisé pour :** Validation des crédits (qui ne doivent pas utiliser les frais de gestion)

#### 11.3. **`TransactionSerializer._calculer_solde_caisse()`**
- **Formule :** `(ENTREE(TOTAL) + ENTREE_APRES_CALCUL_FRAIS_GESTION) - SORTIE(TOTAL)`
- **Utilisé pour :** Validation des transactions SORTIE (vérifie le seuil minimum)

---

## 📊 RÉSUMÉ DES FORMULES PRINCIPALES

1. **Intérêt d'un crédit :** `interet = (montant * taux_interet) / 100`
2. **Frais de gestion :** `frais_gestion = (interet_total_global * pourcentage) / 100`
3. **Intérêt net à répartir :** `interet_net = interet_total_global - frais_gestion_total_global`
4. **Proportion d'un membre :** `proportion = apports_membre / total_apports_global`
5. **Intérêt attribué à un membre :** `interet_membre = interet_net * proportion`
6. **Solde de caisse générale :** `(ENTREE(TOTAL) + ENTREE_APRES_CALCUL_FRAIS_GESTION) - SORTIE(TOTAL)`
7. **Solde disponible par type de caisse :** `Donations + Entrées (hors crédits) - Sorties (hors dépenses) - Crédits actifs`

---

## 🔐 PERMISSIONS PAR ENDPOINT

- **ADMIN/SUPERADMIN :** Accès à tous les calculs
- **MEMBRE :** Accès limité à ses propres calculs (intérêts, frais de gestion, apports, répartition)
- **CLIENT :** Accès limité à ses propres intérêts uniquement (pas de frais de gestion, pas de répartition)

---

## 📝 NOTES IMPORTANTES

1. **Frais de gestion :** Réservés uniquement pour les dépenses, pas pour les crédits
2. **Crédits actifs :** Pour PRECOMPTE, on soustrait `montant_effectif` ; pour POSTCOMPTE, on soustrait `montant`
3. **Période de calcul :** Les apports peuvent être filtrés par mois/année, mais les intérêts sont toujours calculés globalement
4. **Transactions automatiques :** Les frais de gestion créent automatiquement une transaction `ENTREE_APRES_CALCUL_FRAIS_GESTION`
5. **Seuil minimum :** Les crédits et retraits vérifient un seuil minimum de 1 USD sur le solde disponible du type de caisse
