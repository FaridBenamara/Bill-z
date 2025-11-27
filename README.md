# Bill'z - Agent Comptable Automatique

Application web complète pour la gestion comptable automatisée avec IA, destinée aux indépendants et PME.

## 🚀 Fonctionnalités

### 📧 Scan Gmail Automatique

- Extraction automatique des factures depuis Gmail (INBOX + SENT)
- Analyse intelligente avec IA (Groq)
- Détection d'anomalies
- Catégorisation automatique

### 💳 Rapprochement Bancaire

- Import CSV/Excel des transactions bancaires
- Rapprochement automatique avec les factures
- Matching intelligent avec IA (confiance ≥ 85%)
- Confirmation manuelle pour les cas douteux

### 📊 Optimisation Fiscale

- Analyse comptable complète
- Calculs TVA automatiques
- Recommandations personnalisées
- Détection d'opportunités d'économies
- Alertes sur factures à payer / clients à relancer

### 📈 Dashboard

- Vue d'ensemble en temps réel
- Statistiques financières
- Graphiques par catégorie
- Suivi des rapprochements

## 🛠️ Technologies

### Backend

- **FastAPI** - Framework web moderne
- **PostgreSQL** - Base de données
- **SQLAlchemy** - ORM
- **Groq** - API LLM pour l'analyse
- **Google Gmail API** - Scan des emails
- **Pydantic** - Validation des données
- **JWT** - Authentification

### Frontend

- **React** - Framework UI
- **Vite** - Build tool
- **Axios** - Client HTTP
- **Recharts** - Graphiques
- **Lucide React** - Icônes

## 🤖 Architecture Multi-Agents

Bill'z utilise une architecture orchestrée de plusieurs agents IA spécialisés, chacun ayant un rôle précis dans le processus comptable.

### Concept d'Agent

Un **agent** est un système IA spécialisé qui :

- Reçoit des données structurées (factures, transactions, etc.)
- Analyse et traite ces données avec un LLM
- Produit des résultats structurés (JSON)
- Utilise des prompts et contextes spécifiques pour sa tâche

### Les 3 Agents Spécialisés

#### 1. 🧾 Agent Factures

#### 2. 💳 Agent Banque

#### 3. 📊 Agent Optimisation

### Orchestrateur Multi-Agent

**FastAPI** agit comme orchestrateur central qui coordonne les agents :

```
FastAPI (Orchestrateur)
    │
    ├──→ Agent Factures (InvoiceScannerService)
    │       ↓ (sauvegarde en DB et Supabase S3)
    │
    ├──→ Agent Banque (BankReconciliationService)
    │       ↓ (met à jour les transactions)
    │
    └──→ Agent Optimisation (OptimisationService)
            ↓ (analyse globale)
            Dashboard / Recommandations
```

**Flux d'exécution :**

1. **Agent Factures** : FastAPI appelle `InvoiceScannerService` qui scanne Gmail et extrait les factures
2. **Agent Banque** : FastAPI appelle `BankReconciliationService` qui rapproche factures ↔ transactions
3. **Agent Optimisation** : FastAPI appelle `OptimisationService` qui analyse tout et génère des recommandations

**Avantages de cette architecture :**

- **Centralisation** : FastAPI gère toutes les routes API et coordonne les agents
- **Asynchrone** : Les tâches longues (scan Gmail) s'exécutent en arrière-plan
- **Modularité** : Chaque agent est un service indépendant, facile à modifier
- **Communication** : Les agents communiquent via PostgreSQL
- **Scalabilité** : Chaque service peut être optimisé indépendamment

## 📋 Prérequis

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Compte Google (pour Gmail API)
- Clé API Groq

## 🔧 Installation

### 1. Cloner le repository

```bash
git clone https://github.com/votre-repo/bill-z.git
cd bill-z
```

### 2. Backend

```bash
cd backend-api

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Démarrer le serveur
uvicorn app.main:app
```

### 3. Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Démarrer le serveur de développement
npm run dev
```

## ⚙️ Configuration

### Variables d'environnement

Copiez `backend-api/.env.example` vers `backend-api/.env` et configurez :

- `DATABASE_URL` - URL de connexion PostgreSQL
- `SECRET_KEY` - Clé secrète pour l'application
- `JWT_SECRET_KEY` - Clé pour signer les tokens JWT
- `GROQ_API_KEY` - Clé API Groq (obtenez-la sur [console.groq.com](https://console.groq.com))
- `MODEL_NAME_analyse` - Modèle Groq à utiliser

### Gmail OAuth

1. Créez un projet sur [Google Cloud Console](https://console.cloud.google.com)
2. Activez l'API Gmail
3. Créez des credentials OAuth 2.0 (type: Application de bureau)
4. Téléchargez `credentials.json` et placez-le dans `backend-api/`
5. Au premier scan, une fenêtre s'ouvrira pour autoriser l'accès
6. Le `token.json` sera généré automatiquement

## 📁 Structure du projet

```
Bill-z/
├── backend-api/          # API FastAPI
│   ├── app/
│   │   ├── api/          # Routes API
│   │   ├── core/         # Configuration, DB, sécurité
│   │   ├── models/       # Modèles SQLAlchemy
│   │   ├── schemas/      # Schémas Pydantic
│   │   └── services/     # Services métier
│   ├── .env.example      # Template de configuration
│   └── requirements.txt  # Dépendances Python
│
├── frontend/             # Application React
│   ├── src/
│   │   ├── pages/        # Pages de l'application
│   │   ├── components/  # Composants réutilisables
│   │   └── services/     # Services API
│   └── package.json
│
├── agent_factures/       # Contextes et prompts (agent factures)
├── Agent_banque/         # Contextes et prompts (agent banque)
└── Agent_optimisation/   # Contextes et prompts (agent optimisation)
```

## 🎯 Utilisation

### 1. Créer un compte

Allez sur `/signup` et créez un compte.

### 2. Scanner Gmail

- Allez dans "Factures"
- Cliquez sur "Scanner Gmail"
- Autorisez l'accès Gmail si demandé
- Les factures seront extraites automatiquement

### 3. Importer des transactions

- Allez dans "Transactions"
- Cliquez sur "Importer CSV/Excel"
- Sélectionnez votre relevé bancaire
- Les transactions seront importées

### 4. Rapprocher les factures

- Allez dans "Factures"
- Cliquez sur "Rapprocher tout" pour un rapprochement automatique
- Ou cliquez sur le bouton 🔗 d'une facture pour un rapprochement manuel

### 5. Voir les optimisations

- Allez dans "Optimisation"
- Consultez les recommandations fiscales
- Suivez les actions prioritaires

## 💰 Section TVA

### Calculs Automatiques

Bill'z calcule automatiquement votre TVA à partir de vos factures :

- **TVA Collectée** : TVA sur vos factures émises (ventes)
- **TVA Déductible** : TVA sur vos factures reçues (achats)
- **TVA à Payer** : Différence entre collectée et déductible

### Détail par Taux

L'application regroupe vos factures par taux de TVA :

- 20% (taux standard)
- 10% (restauration, transport)
- 5.5% (produits de première nécessité)
- Autres taux spécifiques

Pour chaque taux, vous voyez :

- Nombre de factures
- Total HT
- Total TVA
- Total TTC

### Conseils Personnalisés

L'agent d'optimisation analyse votre situation TVA et vous donne :

- Des alertes sur les dates limites de déclaration
- Des conseils d'optimisation
- Des recommandations pour réduire votre TVA à payer

## 🐛 Dépannage

### Erreur de connexion à la base de données

Vérifiez que PostgreSQL est démarré et que `DATABASE_URL` est correct.

### Erreur Gmail API

Vérifiez que `credentials.json` est présent dans `backend-api/` et que l'API Gmail est activée.

### Erreur Groq API

Vérifiez que `GROQ_API_KEY` est valide et que vous avez des crédits disponibles.

## 📝 Licence

MIT

## 👥 Contributeurs

- **BENAMARA Farid**
- **HAFIANE Fares**
- **HARIGA Skander**
- **ASBANE Amine**
