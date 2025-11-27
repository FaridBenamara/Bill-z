# Architecture - Agent Banque

## Vue d'ensemble
L'agent banque effectue le rapprochement bancaire approximatif entre les factures et les relevés bancaires en utilisant l'IA pour faire correspondre les transactions.

## 🎯 Modélisation visuelle

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT BANQUE                             │
│              Rapprochement Bancaire IA                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐
│  Facture     │         │  Relevé       │
│  JSON        │         │  Bancaire     │
│              │         │  XLSX         │
└──────┬───────┘         └──────┬───────┘
       │                        │
       ▼                        ▼
┌─────────────────────────────────────────┐
│     Préparation des Données             │
│  • read_file (JSON)                     │
│  • pandas.read_excel (XLSX)             │
│  • Conversion en structures Python     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     Chargement Context & Prompt         │
│  • context_envoi.txt (règles métier)   │
│  • prompt.txt (instructions)           │
│  • Remplacement placeholders           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│           Groq API LLM                  │
│  • MODEL_NAME_analyse                   │
│  • Matching flou fournisseur            │
│  • Comparaison montant (±tolérances)    │
│  • Proximité date (mois)                │
│  • Calcul scores confiance               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     Résultat JSON Structuré             │
│  • correspondance_trouvee: bool         │
│  • lignes_correspondantes: [...]        │
│  • similarite_fournisseur: 0.0-1.0      │
│  • ecart_montant, ecart_jours           │
│  • niveau_confiance: 0.0-1.0            │
│  • conclusion: string                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     Affichage Console                   │
│  • Info facture                         │
│  • Lignes correspondantes               │
│  • Détails différences                  │
│  • Niveau confiance                     │
└─────────────────────────────────────────┘

Flux: Facture + Relevé → Préparation → LLM → Résultat → Affichage
```

## Schéma d'architecture détaillé

```mermaid
flowchart TB
    Start([Démarrage Agent Banque]) --> Input1[📄 Facture JSON<br/>- Fournisseur<br/>- Montant TTC<br/>- Date facture<br/>- Devise]
    Start --> Input2[📊 Relevé Bancaire XLSX<br/>- Transactions bancaires<br/>- Date, Montant<br/>- Vendor<br/>- Currency]
    
    Input1 --> Load1[🔧 utils_banque.py<br/>read_file<br/>Lecture du JSON facture]
    Input2 --> Load2[🔧 utils_banque.py<br/>lire_xlsx_en_liste_de_dicos<br/>Pandas: pd.read_excel<br/>Convertit en liste de dictionnaires]
    
    Load1 --> Prepare[📝 load_prompt_and_context<br/>Charge context_envoi.txt<br/>Charge prompt.txt<br/>Remplace placeholders:<br/>{{facture_json}}<br/>{{releve_bancaire}}]
    Load2 --> Prepare
    
    Prepare --> Context[📋 Context System<br/>Agent spécialisé rapprochement<br/>Règles métier:<br/>- Similarité fournisseur ≥ 0.60<br/>- Tolérance montant ±0.50 à ±5<br/>- Proximité date: même mois<br/>- Devise ignorée]
    
    Prepare --> Prompt[💬 Prompt User<br/>Instructions détaillées:<br/>- Matching flou fournisseur<br/>- Comparaison montant<br/>- Proximité temporelle<br/>- Format JSON attendu]
    
    Context --> GroqAPI[🤖 API Groq<br/>client.chat.completions.create<br/>MODEL_NAME_analyse<br/>response_format: json_object]
    Prompt --> GroqAPI
    
    GroqAPI --> Parse{📥 Réponse<br/>JSON valide?}
    
    Parse -->|✅ Oui| Result[JSON Résultat<br/>facture: {...}<br/>correspondance_trouvee: bool<br/>lignes_correspondantes: [...]<br/>conclusion: string]
    
    Parse -->|❌ Non| Error[⚠️ Erreur JSON<br/>Affiche raw_content]
    
    Result --> Output[📤 Sortie<br/>Dictionnaire Python<br/>avec résultats<br/>de rapprochement]
    
    Output --> Display[🖥️ afficher_rapprochement<br/>Formatage console:<br/>- Info facture<br/>- Lignes correspondantes<br/>- Détails différences<br/>- Niveau confiance]
    
    Error --> End([Fin])
    Display --> End
    
    style Start fill:#90EE90
    style GroqAPI fill:#FFD700
    style Result fill:#87CEEB
    style Error fill:#FFB6C1
    style End fill:#90EE90
```

## Outils et technologies utilisés

### 1. **Extraction de données**
- **pandas** (`pd.read_excel`) : Lecture et conversion du fichier XLSX en structures Python
- **read_file** : Lecture des fichiers texte (JSON, context, prompt)

### 2. **LLM - Modèle d'analyse**
- **API Groq** : Service d'inférence LLM haute performance
- **MODEL_NAME_analyse** : Modèle configuré via `.env` (ex: `llama-3.3-70b-versatile`)
- **response_format** : Force la réponse en JSON structuré

### 3. **Traitement des données**
- **JSON** : Sérialisation/désérialisation des données
- **Python dict/list** : Structures de données pour manipulation

## Flux séquentiel détaillé

### Étape 1 : Chargement des entrées
```
1. Lire facture JSON (invoice_sample.json)
   → Convertir en string pour injection dans prompt
   
2. Lire relevé bancaire XLSX (releve_bancaire_08-2017.xlsx)
   → Pandas lit le fichier
   → Conversion en liste de dictionnaires
   → Chaque ligne = transaction bancaire
   → Sérialisation en JSON string
```

### Étape 2 : Préparation du contexte et prompt
```
1. Charger context_envoi.txt
   → Règles métier du rapprochement
   → Critères d'approximation
   → Format de sortie attendu
   
2. Charger prompt.txt
   → Template avec placeholders
   → Instructions spécifiques à la tâche
   
3. Remplacer placeholders
   → {{facture_json}} → JSON facture
   → {{releve_bancaire}} → JSON relevé
```

### Étape 3 : Appel LLM Groq
```
1. Initialiser client Groq
   → API Key depuis .env (GROQ_API_KEY)
   
2. Créer messages conversation
   → Role "system": context (règles métier)
   → Role "user": prompt (données + instructions)
   
3. Appel API
   → model: MODEL_NAME_analyse
   → response_format: {"type": "json_object"}
   → Retourne JSON structuré
```

### Étape 4 : Traitement de la réponse
```
1. Extraire content de la réponse
   → response.choices[0].message.content
   
2. Parser JSON
   → json.loads(raw_content)
   → Validation du format
   
3. Gérer erreurs
   → Si JSON invalide → afficher raw_content
   → Si exception API → logger l'erreur
```

### Étape 5 : Affichage des résultats
```
1. Extraire sections du résultat
   → Informations facture
   → Correspondance trouvée (bool)
   → Lignes correspondantes (array)
   → Conclusion (string)
   
2. Formater pour console
   → Présentation structurée
   → Détails des différences
   → Scores de confiance
```

## Critères de rapprochement (implémentés dans le LLM)

### 1. Similarité Fournisseur
- Matching flou (fuzzy matching)
- Seuil minimum : ≥ 0.60
- Comparaison nom vendor vs fournisseur facture

### 2. Écart Montant
- Tolérances progressives :
  - ±0.50 → Excellent
  - ±1 → Bon
  - ±5 → Acceptable
  - >5 → Faible mais possible

### 3. Proximité Date
- Même mois → Parfait
- Mois suivant → Acceptable
- 2 mois d'écart → Faible
- >3 mois → Très faible

### 4. Devise
- **IGNORÉE** : Ne compte pas dans les différences
- Les montants sont comparés en valeur absolue

## Format de sortie JSON

```json
{
  "facture": {
    "fournisseur": "Nom Fournisseur",
    "montant_ttc": 123.45,
    "date": "2024-01-15",
    "devise": "EUR"
  },
  "correspondance_trouvee": true,
  "lignes_correspondantes": [
    {
      "date": "2024-01",
      "amount": -123.45,
      "currency": "EUR",
      "vendor": "Nom Fournisseur",
      "similarite_fournisseur": 0.95,
      "differences": [],
      "details_differences": {
        "montant_facture": 123.45,
        "montant_releve": -123.45,
        "ecart_montant": 0.0,
        "date_facture": "2024-01-15",
        "date_releve": "2024-01",
        "ecart_jours": 15
      },
      "niveau_confiance": 0.98
    }
  ],
  "conclusion": "Correspondance trouvée avec haute confiance"
}
```

## Configuration requise

### Variables d'environnement (`.env`)
```
GROQ_API_KEY=your_groq_api_key
MODEL_NAME_analyse=llama-3.3-70b-versatile
```

### Dépendances Python
```
pandas>=2.0.0
python-dotenv>=1.0.0
groq>=0.4.0
openpyxl  # Pour pandas.read_excel
```

## Points d'intégration

- **Entrée** : Facture JSON (peut venir de l'agent factures)
- **Sortie** : Résultat de rapprochement (peut être envoyé au backend)
- **Utilisable** : En standalone ou intégré dans un workflow plus large

