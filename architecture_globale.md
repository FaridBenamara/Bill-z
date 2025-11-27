# Architecture Globale - Système Bill'z

## Vue d'ensemble
Bill'z est une plateforme complète de gestion comptable automatisée combinant un frontend React, un backend FastAPI, et trois agents IA spécialisés pour traiter automatiquement les factures, effectuer le rapprochement bancaire, et fournir des analyses et optimisations comptables.

## Schéma d'architecture globale

```mermaid
flowchart TB
    subgraph "🌐 Frontend - React + Vite"
        UI[👤 Interface Utilisateur<br/>React Components<br/>- Dashboard<br/>- Factures<br/>- Transactions<br/>- Settings]
        AuthUI[🔐 Pages Auth<br/>Login / Signup<br/>Token localStorage]
        API_Client[📡 API Client<br/>Axios<br/>Intercepteurs<br/>Bearer Token]
    end
    
    subgraph "🖥️ Backend - FastAPI"
        API_Gateway[🚪 FastAPI App<br/>CORS Middleware<br/>Routes API]
        
        subgraph "🔒 Authentication"
            AuthAPI[/api/auth<br/>- POST /register<br/>- POST /login<br/>- GET /me]
            JWT[🔑 JWT Security<br/>create_access_token<br/>verify_token<br/>Password hashing]
        end
        
        subgraph "📄 Invoice Management"
            InvoiceAPI[/api/invoices<br/>- POST /upload<br/>- GET /<br/>- GET /{id}<br/>- DELETE /{id}<br/>- POST /scan]
            InvoiceService[📊 Invoice Service<br/>Validation<br/>Storage PDF<br/>DB Operations]
        end
        
        subgraph "📊 Optimisation & Analysis"
            OptimAPI[/api/optimisation<br/>- GET /analyze<br/>- GET /tva<br/>- GET /stats]
            OptimService[🔍 Optimisation Service<br/>Analyse comptable<br/>Synthèse financière<br/>Recommandations]
        end
        
        subgraph "💾 Database Layer"
            DB[🗄️ PostgreSQL<br/>Tables:<br/>- users<br/>- invoices<br/>- transactions]
            ORM[🔧 SQLAlchemy<br/>ORM Models<br/>Sessions]
        end
        
        subgraph "📁 Storage"
            FileStorage[💿 File System<br/>uploads/users/{id}/<br/>PDF Factures]
        end
        
        AgentRunner[🤖 Agent Runner Service<br/>run_invoice_agent<br/>Subprocess Manager]
    end
    
    subgraph "🤖 Agent Factures"
        AgentFact[📧 Agent Facture<br/>agent_facture.py<br/>Main Loop]
        
        subgraph "🔧 Tools Agent Factures"
            Gmail[📬 Gmail API<br/>recup_mail.py<br/>OAuth 2.0<br/>INBOX scan]
            PDFExtract[📖 PDF Extraction<br/>pdfplumber<br/>extract_text_from_pdf]
            OCR[🖼️ OCR Images<br/>Mistral Pixtral<br/>extract_text_with_pixtral]
            GroqFact[🤖 Groq LLM<br/>Analyse facture<br/>Extraction JSON]
        end
        
        SendBackend[📤 send_to_backend.py<br/>POST /api/invoices/upload<br/>Multipart upload]
    end
    
    subgraph "🏦 Agent Banque"
        AgentBank[💳 Agent Banque<br/>agent_banque.py<br/>Rapprochement]
        
        subgraph "🔧 Tools Agent Banque"
            ExcelReader[📊 Excel Reader<br/>pandas<br/>read_excel<br/>XLSX → Dict]
            GroqBank[🤖 Groq LLM<br/>Rapprochement<br/>Fuzzy matching<br/>Score confiance]
        end
    end
    
    subgraph "📈 Agent Optimisation"
        AgentOpt[🎯 Agent Optimisation<br/>agent_optimisation.py<br/>Analyse globale]
        
        subgraph "🔧 Tools Agent Optimisation"
            DataPrep[📋 Préparation Données<br/>prepare_facture_json<br/>prepare_rapprochement_json<br/>Normalisation]
            GroqOpt[🤖 Groq LLM<br/>Analyse comptable<br/>Statistiques<br/>Recommandations]
        end
    end
    
    subgraph "☁️ External Services"
        GmailService[📧 Gmail Service<br/>Google Cloud<br/>OAuth 2.0]
        GroqAPI[🚀 Groq API<br/>LLM Inference<br/>Fast inference]
        MistralAPI[🎨 Mistral API<br/>Pixtral Vision<br/>OCR Images]
    end
    
    %% Frontend to Backend
    UI --> API_Client
    AuthUI --> API_Client
    API_Client -->|HTTPS| API_Gateway
    
    %% Backend Internal
    API_Gateway --> AuthAPI
    API_Gateway --> InvoiceAPI
    API_Gateway --> OptimAPI
    AuthAPI --> JWT
    InvoiceAPI --> InvoiceService
    InvoiceService --> ORM
    InvoiceService --> FileStorage
    OptimAPI --> OptimService
    OptimService --> ORM
    ORM --> DB
    InvoiceAPI --> AgentRunner
    
    %% Backend to Agent Factures
    AgentRunner -->|Subprocess<br/>USER_TOKEN env| AgentFact
    AgentFact --> Gmail
    AgentFact --> PDFExtract
    AgentFact --> OCR
    AgentFact --> GroqFact
    AgentFact --> SendBackend
    
    %% Agent Factures to External
    Gmail -->|OAuth| GmailService
    GroqFact -->|API Call| GroqAPI
    OCR -->|API Call| MistralAPI
    
    %% Agent Factures to Backend
    SendBackend -->|HTTP POST<br/>Bearer Token| InvoiceAPI
    
    %% Agent Banque
    AgentBank --> ExcelReader
    AgentBank --> GroqBank
    GroqBank -->|API Call| GroqAPI
    
    %% Agent Optimisation
    OptimService -->|Intégré| AgentOpt
    AgentOpt --> DataPrep
    AgentOpt --> GroqOpt
    DataPrep --> ORM
    GroqOpt -->|API Call| GroqAPI
    
    %% Frontend to Optimisation
    UI -->|GET /optimisation/analyze| OptimAPI
    
    %% Styling
    style UI fill:#61DAFB
    style API_Gateway fill:#009485
    style DB fill:#336791
    style AgentFact fill:#FFD700
    style AgentBank fill:#FFD700
    style AgentOpt fill:#FFD700
    style GroqAPI fill:#FF6B6B
    style MistralAPI fill:#FF6B6B
    style GmailService fill:#4285F4
```

## Flux de données séquentiels

### Flux 1 : Inscription et Authentification

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant F as Frontend React
    participant B as Backend FastAPI
    participant D as PostgreSQL
    
    U->>F: Accès /signup
    U->>F: Remplit formulaire
    F->>B: POST /api/auth/register<br/>{email, password}
    B->>B: Hash password (bcrypt)
    B->>D: INSERT INTO users
    D-->>B: User créé
    B-->>F: 201 Created<br/>{user, token}
    F->>F: localStorage.setItem('token')
    F->>F: Redirection /dashboard
```

### Flux 2 : Scan Gmail et Extraction Factures

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant F as Frontend
    participant B as Backend API
    participant AR as Agent Runner
    participant AF as Agent Factures
    participant G as Gmail API
    participant M as Mistral API
    participant Gr as Groq API
    participant D as Database
    
    U->>F: Clic "Scanner Gmail"
    F->>B: POST /api/invoices/scan<br/>Bearer Token
    B->>B: Créer JWT token
    B->>AR: run_invoice_agent(token)
    AR->>AF: Subprocess<br/>USER_TOKEN=token
    AF->>G: OAuth Gmail<br/>List messages INBOX
    G-->>AF: Emails avec PJ
    loop Pour chaque email
        AF->>AF: Sauvegarder PDF/image temp/
        alt PDF
            AF->>AF: pdfplumber.extract_text()
        else Image
            AF->>M: Pixtral OCR<br/>Extract text
            M-->>AF: Texte extrait
        end
        AF->>Gr: Groq API<br/>Analyse facture<br/>Prompt + Context
        Gr-->>AF: JSON structuré
        AF->>B: POST /api/invoices/upload<br/>PDF + JSON<br/>Bearer Token
        B->>D: Sauvegarder PDF<br/>INSERT invoice
        D-->>B: Invoice créée
        B-->>AF: 201 Created
        AF->>AF: Supprimer temp/
    end
    AF-->>AR: Résultat exécution
    AR-->>B: {success, count}
    B-->>F: 200 OK<br/>{invoices_processed}
    F->>F: Afficher notification
```

### Flux 3 : Rapprochement Bancaire

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant AB as Agent Banque
    participant P as Pandas
    participant Gr as Groq API
    
    U->>AB: Lancer agent_banque.py<br/>Facture JSON + Relevé XLSX
    AB->>P: lire_xlsx_en_liste_de_dicos<br/>pd.read_excel()
    P-->>AB: Liste transactions
    AB->>AB: Charger context + prompt
    AB->>AB: Remplacer placeholders
    AB->>Gr: Groq API<br/>Rapprochement<br/>Facture vs Relevé
    Gr-->>AB: JSON rapprochement<br/>Lignes correspondantes<br/>Scores confiance
    AB->>AB: Afficher résultats
    AB->>U: Console output
```

### Flux 4 : Visualisation Factures

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant F as Frontend
    participant B as Backend
    participant D as Database
    participant FS as File Storage
    
    U->>F: Accès /factures
    F->>B: GET /api/invoices<br/>Bearer Token
    B->>D: SELECT * FROM invoices<br/>WHERE user_id = ?
    D-->>B: Liste invoices
    B-->>F: JSON array invoices
    F->>F: Afficher tableau
    U->>F: Clic "Télécharger PDF"
    F->>B: GET /api/invoices/{id}/pdf
    B->>FS: Lire fichier PDF
    FS-->>B: PDF binaire
    B-->>F: FileResponse PDF
    F->>U: Téléchargement PDF
```

### Flux 5 : Analyse et Optimisation

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant F as Frontend
    participant B as Backend API
    participant OS as Optimisation Service
    participant D as Database
    participant Gr as Groq API
    
    U->>F: Accès /optimisation
    F->>B: GET /api/optimisation/analyze<br/>Bearer Token
    B->>OS: OptimisationService.analyze(user_id)
    OS->>D: SELECT * FROM invoices<br/>WHERE user_id = ?
    D-->>OS: Liste factures
    OS->>D: SELECT * FROM transactions<br/>WHERE user_id = ? AND is_reconciled = TRUE
    D-->>OS: Transactions rapprochées
    OS->>OS: prepare_facture_json<br/>pour chaque facture
    OS->>OS: prepare_rapprochement_json<br/>Mapping facture ↔ transaction
    OS->>OS: json.dumps<br/>factures + rapprochements
    OS->>OS: Charger context.txt + prompt.txt
    OS->>OS: Remplacer {{factures_json}}<br/>{{rapprochements_json}}
    OS->>Gr: Groq API<br/>Analyse comptable globale<br/>System: context<br/>User: prompt + données
    Gr-->>OS: JSON résultat<br/>- statistiques_globales<br/>- rapprochements<br/>- analyse_fournisseurs<br/>- anomalies<br/>- optimisations<br/>- résumé
    OS-->>B: Résultat analyse
    B-->>F: 200 OK<br/>JSON structuré
    F->>F: Afficher dashboard<br/>Statistiques<br/>Graphiques<br/>Recommandations
    F->>U: Interface analyse
```

## Technologies et Stack

### Frontend
- **Framework** : React 18+
- **Build Tool** : Vite
- **Styling** : TailwindCSS
- **UI Components** : shadcn/ui
- **HTTP Client** : Axios
- **Routing** : React Router (implicite)

### Backend
- **Framework** : FastAPI (Python)
- **Database** : PostgreSQL
- **ORM** : SQLAlchemy
- **Authentication** : JWT (python-jose, passlib)
- **File Storage** : File System local
- **CORS** : FastAPI CORS Middleware

### Agents IA
- **Agent Factures**
  - Gmail API (Google)
  - PDF Extraction : pdfplumber
  - OCR Images : Mistral Pixtral
  - LLM Analyse : Groq API
  
- **Agent Banque**
  - Excel Reading : pandas
  - LLM Rapprochement : Groq API
  
- **Agent Optimisation**
  - Data Preparation : Normalisation factures/rapprochements
  - LLM Analyse globale : Groq API
  - Statistiques : Calculs agrégés
  - Recommandations : Analyse financière

### External Services
- **Groq API** : Inférence LLM rapide
- **Mistral API** : Vision multi-modal (Pixtral)
- **Gmail API** : Accès emails Google

## Structure de données

### Base de données PostgreSQL

#### Table `users`
```sql
- id: INTEGER PRIMARY KEY
- email: VARCHAR UNIQUE
- hashed_password: VARCHAR
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### Table `invoices`
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER FOREIGN KEY → users.id
- invoice_number: VARCHAR
- invoice_date: DATE
- due_date: DATE
- supplier: JSONB
- client: JSONB
- amounts: JSONB
- category: VARCHAR
- anomalies: JSONB[]
- confidence_global: FLOAT
- file_path: VARCHAR
- file_name: VARCHAR
- email_id: VARCHAR
- email_subject: VARCHAR
- invoice_type: VARCHAR (entrante/sortante)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### Table `transactions`
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER FOREIGN KEY → users.id
- invoice_id: INTEGER FOREIGN KEY → invoices.id (nullable)
- date: DATE
- amount: DECIMAL
- currency: VARCHAR
- vendor: VARCHAR
- is_reconciled: BOOLEAN
- reconciliation_confidence: FLOAT
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

## Sécurité

### Authentification
- **JWT Tokens** : Access tokens avec expiration
- **Password Hashing** : bcrypt avec salt
- **Bearer Token** : Dans header Authorization

### Autorisation
- **User Isolation** : Chaque utilisateur voit uniquement ses factures
- **Token Validation** : Middleware vérifie token sur chaque requête
- **File Access** : Vérification user_id avant accès PDF

### API Keys
- **Groq API Key** : Stockée en `.env`, jamais commitée
- **Mistral API Key** : Stockée en `.env`
- **Gmail Credentials** : OAuth flow, token.json local

## Déploiement et Configuration

### Variables d'environnement Backend
```env
DATABASE_URL=postgresql://user:pass@localhost/billz
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Variables d'environnement Agents
```env
GROQ_API_KEY=your_groq_key
MODEL_NAME_analyse=llama-3.3-70b-versatile
MISTRAL_API_KEY=your_mistral_key
MODEL_NAME_extract=pixtral-12b-latest
USER_TOKEN=optional_backend_token
```

### Frontend Configuration
```env
VITE_API_URL=http://localhost:8000
```

## Points d'intégration

### Frontend ↔ Backend
- **REST API** : Communication HTTP/JSON
- **JWT Tokens** : Authentification stateless
- **CORS** : Configuré pour développement/production

### Backend ↔ Agent Factures
- **Subprocess** : Backend lance agent en subprocess
- **Environment Variable** : USER_TOKEN passé via env
- **HTTP Upload** : Agent envoie résultats via API

### Agent Factures ↔ Services Externes
- **Gmail API** : OAuth 2.0, accès en lecture
- **Groq API** : Clé API, requêtes synchrones
- **Mistral API** : Clé API, OCR vision

### Agent Banque
- **Standalone** : Utilisable indépendamment
- **Input** : Fichiers locaux (JSON + XLSX)
- **Output** : Console + JSON résultat

## Scalabilité et Performance

### Optimisations actuelles
- **Pagination Gmail** : Traitement par lots de 100
- **Async Backend** : FastAPI async/await
- **File Cleanup** : Suppression fichiers temp après upload
- **Connection Pooling** : SQLAlchemy pool de connexions

### Améliorations possibles
- **Queue System** : Redis/Celery pour agents asynchrones
- **Caching** : Redis pour requêtes fréquentes
- **CDN** : Pour servir PDFs
- **Load Balancer** : Pour backend horizontal scaling

## Monitoring et Logs

### Logs Backend
- FastAPI logging intégré
- Erreurs capturées et retournées JSON

### Logs Agents
- Print statements console
- Erreurs API loggées
- Compteurs factures traitées

### Métriques possibles
- Nombre factures traitées
- Taux d'erreur extraction
- Temps traitement moyen
- Utilisation APIs externes

