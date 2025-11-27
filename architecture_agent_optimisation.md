# Architecture - Agent Optimisation

## Vue d'ensemble
L'agent optimisation effectue une analyse comptable globale en synthétisant les données des factures et leurs rapprochements bancaires. Il génère des statistiques, détecte des anomalies, et propose des recommandations d'optimisation financière.

## 🎯 Modélisation visuelle

```
┌─────────────────────────────────────────────────────────────┐
│                AGENT OPTIMISATION                            │
│          Analyse Comptable Globale & Synthèse                │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   Mode Standalone    │         │   Mode Backend      │
│                      │         │                     │
│  Factures JSON       │         │  GET /optimisation/ │
│  Rapprochements JSON │         │  analyze            │
│  (manuels)           │         │  JWT Auth           │
└──────────┬───────────┘         └──────────┬──────────┘
           │                                │
           │                                ▼
           │                    ┌──────────────────────┐
           │                    │   PostgreSQL DB     │
           │                    │  • SELECT invoices  │
           │                    │  • SELECT transac.  │
           │                    └──────────┬──────────┘
           │                                │
           └────────────┬───────────────────┘
                        ▼
        ┌───────────────────────────────────────┐
        │     Préparation & Normalisation        │
        │  • prepare_facture_json                │
        │  • prepare_rapprochement_json          │
        │  • Génération facture_id               │
        │  • Mapping facture ↔ transaction       │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │     Construction JSON                  │
        │  • Liste factures normalisées         │
        │  • Liste rapprochements normalisés     │
        │  • json.dumps (ensure_ascii=False)    │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │     Chargement Context & Prompt        │
        │  • context.txt (règles analyse)       │
        │  • prompt.txt (instructions)          │
        │  • Remplacement placeholders          │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │           Groq API LLM                 │
        │  • Analyse comptable globale           │
        │  • Calcul statistiques                 │
        │  • Analyse par fournisseur             │
        │  • Détection anomalies                 │
        │  • Génération recommandations          │
        └───────────────┬───────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────────┐
        │     Résultat JSON Structuré            │
        │  • statistiques_globales              │
        │  • rapprochements (rapprochées/non)   │
        │  • analyse_fournisseurs               │
        │  • anomalies (dédupliquées)            │
        │  • optimisations (recommandations)    │
        │  • résumé                              │
        └───────────────┬───────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────────┐         ┌──────────────────┐
│  Standalone:     │         │  Backend:         │
│  Console Output  │         │  JSON Response    │
│  Formaté         │         │  API 200 OK       │
└──────────────────┘         └──────────────────┘

Flux: Données → Normalisation → LLM Analyse → Résultat → Affichage/API
```

## Schéma d'architecture détaillé

```mermaid
flowchart TB
    Start([🚀 Démarrage Agent Optimisation]) --> Source{📊 Source des données}
    
    Source -->|Standalone| ManualInput[📥 Entrée Manuelle<br/>Factures JSON<br/>Rapprochements JSON<br/>Préparés manuellement]
    
    Source -->|Backend| BackendAPI[🖥️ Backend API<br/>GET /api/optimisation/analyze<br/>JWT Authentication<br/>User ID]
    
    BackendAPI --> DBQuery[🗄️ Requête Database<br/>PostgreSQL<br/>SELECT invoices<br/>SELECT transactions<br/>WHERE user_id = ?]
    
    DBQuery --> FetchInvoices[📄 Récupération Factures<br/>Invoice Model<br/>- invoice_number<br/>- supplier, client<br/>- amounts HT/TVA/TTC<br/>- category, anomalies<br/>- invoice_type<br/>- confidence_global]
    
    DBQuery --> FetchTransactions[💳 Récupération Transactions<br/>Transaction Model<br/>- is_reconciled<br/>- date<br/>- amount<br/>- reconciliation_confidence]
    
    ManualInput --> PrepareFactures[🔧 Préparation Données<br/>prepare_facture_json<br/>Normalisation structure<br/>Génération facture_id]
    FetchInvoices --> PrepareFactures
    
    PrepareFactures --> FactureStruct[📋 Structure Facture<br/>id: facture_id<br/>numero, fournisseur<br/>date, date_echeance<br/>montant_ttc, devise<br/>categorie, invoice_type<br/>anomalies, confiance]
    
    ManualInput --> PrepareRapprochements[🔧 Préparation Rapprochements<br/>prepare_rapprochement_json<br/>Mapping facture_id<br/>État rapprochement]
    FetchTransactions --> PrepareRapprochements
    
    PrepareRapprochements --> RapprochementStruct[🔗 Structure Rapprochement<br/>facture_id<br/>rapprochee: bool<br/>date_paiement<br/>ecart_montant<br/>ecart_jours<br/>niveau_confiance]
    
    FactureStruct --> BuildJSON[📦 Construction JSON<br/>Liste factures<br/>json.dumps<br/>ensure_ascii=False]
    RapprochementStruct --> BuildJSON
    
    BuildJSON --> FacturesJSON[📄 factures_json_str<br/>Array de factures<br/>normalisées]
    
    BuildJSON --> RapprochementsJSON[📊 rapprochements_json_str<br/>Array de rapprochements<br/>normalisés]
    
    FacturesJSON --> LoadContext[📝 Chargement Context<br/>load_prompt_and_context<br/>read_file context.txt]
    RapprochementsJSON --> LoadContext
    
    LoadContext --> SystemContext[📋 Context System<br/>Agent spécialisé<br/>analyse comptable globale<br/>Règles:<br/>- Format JSON strict<br/>- Statistiques globales<br/>- Analyse fournisseurs<br/>- Détection anomalies<br/>- Recommandations<br/>- Normalisation français]
    
    LoadContext --> LoadPrompt[📝 Chargement Prompt<br/>read_file prompt.txt<br/>Template avec placeholders]
    
    LoadPrompt --> ReplacePlaceholders[🔄 Remplacement Placeholders<br/>{{factures_json}}<br/>{{rapprochements_json}}<br/>Injection données]
    
    ReplacePlaceholders --> UserPrompt[💬 Prompt User<br/>Instructions analyse:<br/>- Statistiques globales<br/>- Liste rapprochements<br/>- Analyse par fournisseur<br/>- Anomalies globales<br/>- Optimisations<br/>- Résumé]
    
    SystemContext --> GroqAPI[🤖 Groq API<br/>client.chat.completions.create<br/>MODEL_NAME_analyse<br/>response_format: json_object]
    UserPrompt --> GroqAPI
    
    GroqAPI --> ParseJSON{📥 Réponse<br/>JSON valide?}
    
    ParseJSON -->|✅ Oui| Result[JSON Résultat<br/>statistiques_globales<br/>rapprochements<br/>analyse_fournisseurs<br/>anomalies<br/>optimisations<br/>résumé]
    
    ParseJSON -->|❌ Non| ErrorLog[⚠️ Log Erreur<br/>Affiche raw_content<br/>Return None]
    
    Result --> ProcessResult[🔄 Traitement Résultat<br/>Validation structure<br/>Vérification champs<br/>Formatage données]
    
    ProcessResult --> Output{📤 Mode de sortie}
    
    Output -->|Standalone| DisplayConsole[🖥️ Affichage Console<br/>print_results_global<br/>Formatage lisible<br/>Sections:<br/>- Statistiques<br/>- Rapprochements<br/>- Analyse fournisseurs<br/>- Anomalies<br/>- Optimisations<br/>- Résumé]
    
    Output -->|Backend| ReturnAPI[🌐 Retour API<br/>JSON Response<br/>200 OK<br/>Données structurées]
    
    DisplayConsole --> End([✅ Fin])
    ReturnAPI --> End
    ErrorLog --> End
    
    style Start fill:#90EE90
    style GroqAPI fill:#FFD700
    style Result fill:#87CEEB
    style ErrorLog fill:#FFB6C1
    style BackendAPI fill:#DDA0DD
    style DBQuery fill:#336791
    style End fill:#90EE90
```

## Outils et technologies utilisés

### 1. **Source de données**
- **PostgreSQL Database** : Stockage des factures et transactions
- **SQLAlchemy ORM** : Accès aux données via modèles Python
- **Invoice Model** : Modèle de données factures
- **Transaction Model** : Modèle de données transactions bancaires

### 2. **Préparation des données**
- **prepare_facture_json** : Normalise les données factures
  - Génère un `facture_id` unique (format: `F_{fournisseur}_{numero}`)
  - Extrait les champs essentiels
  - Gère les valeurs nulles
  
- **prepare_rapprochement_json** : Normalise les rapprochements
  - Mappe facture_id avec transaction
  - Calcule écarts montant/jours
  - Détermine état rapprochement (True/False)

### 3. **LLM - Modèle d'analyse**
- **Groq API** : Service d'inférence LLM rapide
- **MODEL_NAME_analyse** : Modèle configuré via `.env` (ex: `llama-3.3-70b-versatile`)
- **response_format** : Force la réponse en JSON structuré

### 4. **Traitement JSON**
- **json.dumps** : Sérialisation avec `ensure_ascii=False` pour caractères français
- **json.loads** : Désérialisation et validation

## Flux séquentiel détaillé

### Étape 1 : Collecte des données

#### Mode Standalone
```
1. Données manuelles fournies
   → Factures brut (dict Python)
   → Rapprochements brut (dict Python)
   
2. Préparation manuelle
   → prepare_facture_json() pour chaque facture
   → prepare_rapprochement_json() pour chaque rapprochement
```

#### Mode Backend (via API)
```
1. Requête utilisateur
   → GET /api/optimisation/analyze
   → JWT Token dans header
   → Extraction user_id
   
2. Requête base de données
   → SELECT * FROM invoices WHERE user_id = ?
   → SELECT * FROM transactions WHERE user_id = ? AND is_reconciled = TRUE
   
3. Mapping données
   → Créer transaction_map (invoice_id → transaction)
   → Préparer factures_data
   → Préparer rapprochements_data
```

### Étape 2 : Normalisation des données

#### Préparation Factures
```
Pour chaque facture:
  1. Extraire champs
     → supplier.name → fournisseur
     → amounts.ttc → montant_ttc
     → amounts.currency → devise
     
  2. Générer ID unique
     → Format: F_{fournisseur_clean}_{invoice_num}
     → Nettoyage caractères spéciaux
     → Limite 25 caractères
     
  3. Construire structure
     {
       "id": "F_ArgonautDiner_NO_NUM",
       "numero": "F2025-050",
       "fournisseur": "Argonaut Diner",
       "date": "2017-08-13",
       "date_echeance": null,
       "montant_ttc": 26.38,
       "devise": "USD",
       "categorie": "restauration / repas",
       "invoice_type": "reçue",
       "anomalies": [],
       "confiance": 1.0
     }
```

#### Préparation Rapprochements
```
Pour chaque facture:
  1. Chercher transaction associée
     → transaction_map.get(invoice.id)
     
  2. Si rapprochée (transaction exists)
     → Calculer écart_montant
     → Calculer écart_jours
     → Extraire niveau_confiance
     
  3. Si non rapprochée
     → rapprochee: False
     → Tous champs null sauf facture_id
     
  4. Structure
     {
       "facture_id": "F_ArgonautDiner_NO_NUM",
       "rapprochee": True,
       "date_paiement": "2017-08",
       "ecart_montant": 0.0,
       "ecart_jours": 0,
       "niveau_confiance": 0.95
     }
```

### Étape 3 : Construction JSON
```
1. Créer listes
   → factures_list = [facture1, facture2, ...]
   → rapprochements_list = [rapp1, rapp2, ...]
   
2. Sérialiser en JSON
   → factures_json_str = json.dumps(factures_list, ensure_ascii=False)
   → rapprochements_json_str = json.dumps(rapprochements_list, ensure_ascii=False)
```

### Étape 4 : Chargement contexte et prompt
```
1. Charger context.txt
   → Règles métier de l'analyse
   → Format de sortie attendu
   → Instructions de normalisation
   
2. Charger prompt.txt
   → Template avec {{factures_json}}
   → Template avec {{rapprochements_json}}
   
3. Remplacer placeholders
   → Injecter factures_json_str
   → Injecter rapprochements_json_str
```

### Étape 5 : Appel LLM Groq
```
1. Initialiser client Groq
   → API Key depuis .env (GROQ_API_KEY)
   
2. Créer messages conversation
   → Role "system": context (règles analyse)
   → Role "user": prompt (données + instructions)
   
3. Appel API
   → model: MODEL_NAME_analyse
   → response_format: {"type": "json_object"}
   → Retourne JSON structuré
```

### Étape 6 : Traitement de la réponse
```
1. Extraire content
   → response.choices[0].message.content
   
2. Parser JSON
   → json.loads(raw_content)
   → Validation structure
   
3. Gérer erreurs
   → Si JSON invalide → logger raw_content
   → Si exception API → logger erreur
```

### Étape 7 : Affichage/Renvoi

#### Mode Standalone
```
1. Appeler print_results_global()
   → Afficher statistiques_globales
   → Afficher rapprochements (rapprochées/non)
   → Afficher analyse_fournisseurs (détaillée)
   → Afficher anomalies_globales
   → Afficher optimisations
   → Afficher résumé
```

#### Mode Backend
```
1. Retourner JSON
   → 200 OK avec résultat complet
   → Frontend affiche dans interface
```

## Structure de sortie JSON

### Statistiques Globales
```json
{
  "statistiques_globales": {
    "nombre_factures_total": 10,
    "nombre_factures_reçues": 7,
    "nombre_factures_envoyées": 3,
    "nombre_fournisseurs": 5,
    "total_factures": 15750.38,
    "total_rapproché": 12300.50,
    "total_non_rapproché": 3449.88,
    "taux_rapprochement": 78.1
  }
}
```

### Rapprochements
```json
{
  "rapprochements": {
    "factures_rapprochées": [
      "F_ArgonautDiner_NO_NUM",
      "F_AlteviaSolutions_F2025-050"
    ],
    "factures_non_rapprochées": [
      "F_AutreFournisseur_123"
    ]
  }
}
```

### Analyse Fournisseurs
```json
{
  "analyse_fournisseurs": [
    {
      "fournisseur": "Argonaut Diner",
      "nombre_factures": 3,
      "total_depenses": 89.14,
      "moyenne_depense": 29.71,
      "depense_max": {
        "facture_id": "F_ArgonautDiner_001",
        "montant": 35.50
      },
      "factures_associees": [
        "F_ArgonautDiner_NO_NUM",
        "F_ArgonautDiner_001"
      ],
      "anomalies_fournisseur": [
        "absence de numéro de facture"
      ]
    }
  ]
}
```

### Anomalies et Optimisations
```json
{
  "anomalies": [
    "absence de numéro de facture",
    "absence de date d'échéance",
    "facture non rapprochée bancairement"
  ],
  "optimisations": [
    "Négocier des conditions de paiement plus longues avec les fournisseurs récurrents",
    "Centraliser les achats pour bénéficier de remises",
    "Améliorer le suivi des factures non rapprochées"
  ],
  "résumé": "Analyse de 10 factures: 78% rapprochées, 5 fournisseurs principaux, quelques anomalies mineures détectées."
}
```

## Types d'analyses effectuées

### 1. Statistiques Globales
- Nombre total de factures (reçues/envoyées)
- Nombre de fournisseurs distincts
- Totaux financiers (TTC)
- Taux de rapprochement bancaire
- Répartition factures reçues vs envoyées

### 2. Analyse par Fournisseur
- Nombre de factures par fournisseur
- Total des dépenses
- Dépense moyenne
- Dépense maximale (avec ID facture)
- Liste des factures associées
- Anomalies spécifiques au fournisseur

### 3. État des Rapprochements
- Liste des factures rapprochées (avec transactions bancaires)
- Liste des factures non rapprochées
- Identification des factures en attente

### 4. Détection d'Anomalies
- Normalisation en français
- Déduplication des anomalies
- Regroupement par type
- Identification des problèmes récurrents

### 5. Recommandations d'Optimisation
- Suggestions financières personnalisées
- Optimisation fiscale
- Amélioration gestion trésorerie
- Négociation fournisseurs

## Configuration requise

### Variables d'environnement (`.env`)
```
GROQ_API_KEY=your_groq_api_key
MODEL_NAME_analyse=llama-3.3-70b-versatile
DATABASE_URL=postgresql://user:pass@localhost/billz
```

### Dépendances Python
```
groq>=0.4.0
sqlalchemy>=2.0.0
python-dotenv>=1.0.0
```

### Fichiers requis
- `Agent_optimisation/context.txt` : Règles métier et format
- `Agent_optimisation/prompt.txt` : Template de prompt

## Points d'intégration

### Mode Standalone
- **Entrée** : Factures et rapprochements en Python dict
- **Sortie** : Affichage console formaté
- **Utilisation** : Analyse ponctuelle de données

### Mode Backend (API)
- **Endpoint** : `GET /api/optimisation/analyze`
- **Authentication** : JWT Bearer Token
- **Entrée** : User ID (depuis token)
- **Sortie** : JSON structuré pour frontend
- **Intégration** : Service Python appelable depuis FastAPI

### Endpoints Backend supplémentaires
- `GET /api/optimisation/tva` : Analyse TVA spécifique
- `GET /api/optimisation/stats` : Statistiques rapides (sans LLM)

## Gestion d'erreurs

1. **Erreur base de données**
   → Retourne structure vide avec message d'erreur

2. **Erreur API Groq**
   → Log erreur, retourne None (Backend) ou affiche erreur (Standalone)

3. **JSON invalide**
   → Affiche raw_content pour debug
   → Retourne None

4. **Données manquantes**
   → Gère valeurs nulles gracieusement
   → Utilise valeurs par défaut

## Cas d'usage

### 1. Analyse mensuelle
Utilisateur lance analyse via interface → Backend récupère toutes ses factures → Analyse complète → Affichage dashboard

### 2. Audit ponctuel
Développeur lance agent standalone → Fournit données test → Analyse complète → Rapport console

### 3. Monitoring continu
Frontend appelle `/api/optimisation/stats` régulièrement → Statistiques rapides sans LLM → Mise à jour temps réel

