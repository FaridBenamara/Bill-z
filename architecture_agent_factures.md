# Architecture - Agent Factures

## Vue d'ensemble
L'agent factures automatise la récupération, l'extraction et l'analyse des factures depuis Gmail en utilisant plusieurs outils d'IA et d'OCR pour transformer les pièces jointes en données structurées.

## 🎯 Modélisation visuelle

```
┌─────────────────────────────────────────────────────────────┐
│                  AGENT FACTURES                              │
│         Extraction & Analyse Automatique                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Gmail INBOX                               │
│  • OAuth 2.0 Authentication                                 │
│  • Scan emails avec pièces jointes                          │
│  • Pagination automatique (100/page)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Extraction Pièces Jointes                       │
│                                                              │
│  ┌──────────────┐              ┌──────────────┐            │
│  │   PDF        │              │   Image      │            │
│  │              │              │   JPG/PNG    │            │
│  └──────┬───────┘              └──────┬───────┘            │
│         │                             │                     │
│         ▼                             ▼                     │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ pdfplumber   │              │ Mistral      │            │
│  │ extract_text │              │ Pixtral OCR  │            │
│  └──────┬───────┘              └──────┬───────┘            │
│         │                             │                     │
│         └──────────────┬───────────────┘                     │
│                       ▼                                     │
│              Texte brut facture                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Analyse avec Groq LLM                           │
│  • context.txt (règles extraction)                          │
│  • prompt.txt (instructions)                                │
│  • Extraction données structurées                           │
│  • Détection anomalies                                     │
│  • Catégorisation métier                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Données Facture JSON                               │
│  • invoice_number, dates                                    │
│  • supplier, client (SIRET, TVA)                           │
│  • amounts (HT, TVA, TTC)                                  │
│  • category, anomalies                                     │
│  • confidence_global                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Envoi au Backend                                │
│  • POST /api/invoices/upload                               │
│  • Multipart: PDF + JSON                                    │
│  • JWT Bearer Token                                         │
│  • Sauvegarde PostgreSQL                                    │
└─────────────────────────────────────────────────────────────┘

Flux: Gmail → Extraction (PDF/OCR) → LLM Analyse → Backend → DB
```

## Schéma d'architecture détaillé

```mermaid
flowchart TB
    Start([🚀 Démarrage Agent Factures]) --> Auth[🔐 Authentification Gmail<br/>recup_mail.py<br/>Google OAuth 2.0<br/>Token: token.json<br/>Credentials: credentials.json]
    
    Auth --> GmailAPI[📧 Gmail API<br/>service.users.messages.list<br/>Label: INBOX<br/>Pagination automatique<br/>Max 100 par page]
    
    GmailAPI --> Filter[🔍 Filtrage Emails<br/>Avec pièces jointes uniquement<br/>Parcours récursif parts<br/>Détection attachments]
    
    Filter --> Loop{📬 Pour chaque email}
    
    Loop --> ExtractAtt[📎 Extraction Attachments<br/>Base64 decode<br/>Sauvegarde temp/<br/>filename, data binary]
    
    ExtractAtt --> CheckType{📄 Type fichier?}
    
    CheckType -->|PDF| PDFExtract[📖 Extraction PDF<br/>utils_facture.py<br/>pdfplumber.open<br/>extract_text_from_pdf<br/>Page par page]
    
    CheckType -->|Image JPG/PNG| ImageExtract[🖼️ Extraction Image<br/>utils_facture.py<br/>extract_text_with_pixtral<br/>Encode base64<br/>Mistral Pixtral API]
    
    PDFExtract --> TextClean[🧹 Nettoyage Texte<br/>strip, trim<br/>Normalisation<br/>Texte brut]
    ImageExtract --> TextClean
    
    TextClean --> PreparePrompt[📝 Préparation Prompt<br/>load_prompt_and_context<br/>Charge context.txt<br/>Charge prompt.txt<br/>Remplace {{FACTURE_BRUTE}}]
    
    PreparePrompt --> SystemContext[📋 Context System<br/>Agent spécialisé factures<br/>Règles strictes:<br/>- Ne pas inventer<br/>- null si absent<br/>- Détection anomalies<br/>- Catégorisation métier]
    
    PreparePrompt --> UserPrompt[💬 Prompt User<br/>Texte brut facture<br/>Instructions extraction<br/>Format JSON attendu]
    
    SystemContext --> GroqAnalyze[🤖 Groq API - Analyse<br/>analyze_text<br/>model: MODEL_NAME_analyse<br/>response_format: json_object<br/>Temperature: default]
    UserPrompt --> GroqAnalyze
    
    GroqAnalyze --> ParseJSON{📥 JSON valide?}
    
    ParseJSON -->|✅ Oui| InvoiceData[📊 Données Facture<br/>invoice_number<br/>invoice_date, due_date<br/>supplier, client<br/>amounts HT/TVA/TTC<br/>category, anomalies<br/>confidence_global]
    
    ParseJSON -->|❌ Non| ErrorLog[⚠️ Log Erreur<br/>Affiche raw_content<br/>Skip cette facture]
    
    InvoiceData --> CheckToken{🔑 Token Backend?}
    
    CheckToken -->|✅ Oui| SendBackend[📤 Envoi Backend<br/>send_to_backend.py<br/>POST /api/invoices/upload<br/>Multipart: PDF + JSON<br/>Bearer Token Auth]
    
    CheckToken -->|❌ Non| LogOnly[📝 Log uniquement<br/>Aucun upload<br/>Données conservées localement]
    
    SendBackend --> BackendAPI[🖥️ Backend FastAPI<br/>Upload endpoint<br/>Validation données<br/>Sauvegarde PDF<br/>Insertion PostgreSQL]
    
    BackendAPI --> Cleanup[🗑️ Nettoyage<br/>Supprime temp/filename<br/>Garde uniquement en DB]
    
    Cleanup --> NextEmail{📬 Email suivant?}
    ErrorLog --> NextEmail
    LogOnly --> NextEmail
    
    NextEmail -->|Oui| Loop
    NextEmail -->|Non| End([✅ Fin Traitement])
    
    style Start fill:#90EE90
    style GmailAPI fill:#FFD700
    style PDFExtract fill:#87CEEB
    style ImageExtract fill:#87CEEB
    style GroqAnalyze fill:#FFD700
    style InvoiceData fill:#98FB98
    style BackendAPI fill:#DDA0DD
    style ErrorLog fill:#FFB6C1
    style End fill:#90EE90
```

## Outils et technologies utilisés

### 1. **Récupération emails**
- **Gmail API v1** : Accès aux emails
- **Google OAuth 2.0** : Authentification sécurisée
- **token.json** : Token de session sauvegardé
- **credentials.json** : Clés OAuth client

### 2. **Extraction de texte PDF**
- **pdfplumber** : Bibliothèque Python spécialisée
- **Méthode** : `pdf.extract_text()` page par page
- **Avantages** : Préserve la structure, gère les tableaux

### 3. **Extraction de texte Images (OCR)**
- **Mistral Pixtral API** : Modèle vision multi-modal
- **MODEL_NAME_extract** : `pixtral-12b-latest`
- **Processus** :
  - Encode image en base64
  - Envoie à l'API avec prompt
  - Retourne texte extrait

### 4. **Analyse LLM**
- **Groq API** : Service d'inférence rapide
- **MODEL_NAME_analyse** : Modèle configuré (ex: `llama-3.3-70b-versatile`)
- **Format** : JSON structuré forcé

### 5. **Communication Backend**
- **requests** : HTTP client Python
- **Multipart/form-data** : Upload PDF + JSON
- **JWT Bearer Token** : Authentification utilisateur

## Flux séquentiel détaillé

### Étape 1 : Authentification Gmail
```
1. Vérifier token.json existe
   → Si oui: charger credentials
   → Si expiré: refresh avec refresh_token
   
2. Si pas de token
   → Lancer OAuth flow
   → Ouvrir navigateur
   → Autoriser accès Gmail
   → Sauvegarder token.json
   
3. Construire service Gmail
   → build('gmail', 'v1', credentials)
```

### Étape 2 : Récupération emails avec pagination
```
1. Premier appel messages.list
   → labelIds: ['INBOX']
   → maxResults: 100
   
2. Boucle pagination
   → Si nextPageToken existe
   → Relancer avec pageToken
   → Accumuler tous les messages
   
3. Pour chaque message ID
   → Appel messages.get(format='full')
   → Extraire headers, payload
```

### Étape 3 : Extraction pièces jointes
```
1. Parcourir payload.parts récursivement
   → Si part.filename existe
   → Récupérer attachmentId
   
2. Appel attachments.get
   → Décoder base64urlsafe
   → Créer dict {filename, data}
   
3. Filtrer emails avec attachments
   → Ignorer emails sans PJ
```

### Étape 4 : Traitement par pièce jointe
```
Pour chaque attachment:
  1. Déterminer type
     → .pdf → PDF
     → .jpg/.png → Image
     
  2. Sauvegarder dans temp/
     → Écrire data binaire
     
  3. Extraction texte
     → PDF: pdfplumber
     → Image: Mistral Pixtral
     
  4. Nettoyer texte
     → strip whitespace
     → Préparer pour LLM
```

### Étape 5 : Analyse avec LLM Groq
```
1. Charger context.txt
   → Règles métier
   → Champs à extraire
   → Détection anomalies
   
2. Charger prompt.txt
   → Template avec {{FACTURE_BRUTE}}
   → Remplacer par texte extrait
   
3. Appel API Groq
   → system: context
   → user: prompt avec texte
   → response_format: json_object
   
4. Parser réponse
   → json.loads(content)
   → Validation structure
```

### Étape 6 : Envoi au backend (si token disponible)
```
1. Préparer données
   → Ajouter email_id
   → Ajouter email_subject
   → Formater JSON
   
2. Requête POST multipart
   → file: PDF binaire
   → extracted_data: JSON string
   → Authorization: Bearer token
   
3. Gérer réponse
   → 201: Succès → Afficher ID
   → Autre: Erreur → Logger
   
4. Nettoyage
   → Supprimer temp/filename
   → Garder uniquement en DB
```

## Extraction de données structurées

### Champs extraits

#### Informations facture
- `invoice_number` : Numéro facture
- `invoice_date` : Date émission (YYYY-MM-DD)
- `due_date` : Date échéance

#### Fournisseur (supplier)
- `name` : Nom fournisseur
- `siret` : Numéro SIRET
- `vat` : Numéro TVA intracom

#### Client
- `name` : Nom client
- `siret` : Numéro SIRET client
- `vat` : Numéro TVA client

#### Montants (amounts)
- `ht` : Montant Hors Taxes
- `tva` : Montant TVA
- `tva_rate` : Taux TVA (%)
- `ttc` : Montant Toutes Taxes Comprises
- `currency` : Devise (défaut: EUR)

#### Métadonnées
- `category` : Catégorie métier (software, infrastructure, telecom, etc.)
- `anomalies` : Liste des anomalies détectées
- `confidence_global` : Score de confiance (0-1)

## Catégorisation métier

L'agent catégorise automatiquement selon le contenu :
- `software` : Logiciels, licences
- `infrastructure / hosting / cloud` : Hébergement, cloud
- `SaaS / abonnement` : Services récurrents
- `marketing / publicité` : Campagnes pub
- `telecom` : Télécommunications
- `matériel / hardware` : Équipements
- `restauration / repas` : Restaurants, traiteurs
- `transport / mobilité` : Transport, déplacement
- `consulting / prestation` : Prestations intellectuelles
- `formation` : Formations
- `assurance` : Assurances
- `energie` : Énergie, électricité
- `maintenance` : Maintenance
- `autre` : Non catégorisé

## Détection d'anomalies

### Types d'anomalies détectées
- Absence numéro facture
- Absence mention légale (SIRET, TVA)
- Incohérence montants (HT + TVA ≠ TTC)
- Arrondis incorrects
- Date échéance avant date facture
- Devise manquante
- Montant nul ou négatif
- Format incohérent

## Configuration requise

### Variables d'environnement (`.env`)
```
GROQ_API_KEY=your_groq_api_key
MODEL_NAME_analyse=llama-3.3-70b-versatile
MISTRAL_API_KEY=your_mistral_api_key
MODEL_NAME_extract=pixtral-12b-latest
USER_TOKEN=optional_jwt_token
```

### Fichiers OAuth Gmail
- `credentials.json` : Clés OAuth (depuis Google Cloud Console)
- `token.json` : Généré automatiquement après première auth

### Dépendances Python
```
groq>=0.4.0
mistralai>=0.1.0
pdfplumber>=0.10.0
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-api-python-client>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## Points d'intégration

### Entrée
- **Gmail INBOX** : Emails avec pièces jointes PDF/images

### Sortie
- **Backend API** : `/api/invoices/upload`
  - PDF sauvegardé sur disque
  - Données JSON en PostgreSQL
  - Lien avec utilisateur (user_id)

### Utilisation
- **Standalone** : `python agent_facture.py`
- **Via Backend** : Endpoint `/api/invoices/scan` lance l'agent
- **Token utilisateur** : Passé via env ou paramètre

## Gestion d'erreurs

1. **Erreur authentification Gmail**
   → Ré-authentification OAuth

2. **Erreur extraction PDF/Image**
   → Skip cette PJ, continue suivante

3. **Erreur API Groq/Mistral**
   → Log erreur, skip facture

4. **Erreur backend upload**
   → Données conservées localement
   → Peut réessayer plus tard

5. **Timeout**
   → Agent peut être relancé
   → Gmail API gère la pagination

