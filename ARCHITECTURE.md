# 📐 Architecture du Système Bill'z

Ce document présente l'architecture complète du système Bill'z, une plateforme de gestion comptable automatisée utilisant l'IA.

## 📚 Documentation d'architecture

### 1. [Architecture Agent Banque](./architecture_agent_banque.md)
Schéma détaillé de l'agent de rapprochement bancaire :
- Flux séquentiel complet
- Outils utilisés (pandas, Groq API)
- Critères de rapprochement
- Format de sortie

### 2. [Architecture Agent Factures](./architecture_agent_factures.md)
Schéma détaillé de l'agent d'extraction de factures :
- Pipeline Gmail → Extraction → Analyse → Backend
- Outils utilisés (Gmail API, pdfplumber, Mistral Pixtral, Groq)
- Gestion des PDF et images
- Détection d'anomalies

### 3. [Architecture Agent Optimisation](./architecture_agent_optimisation.md)
Schéma détaillé de l'agent d'analyse et d'optimisation :
- Analyse comptable globale
- Statistiques et synthèse financière
- Recommandations d'optimisation
- Intégration backend

### 4. [Architecture Globale](./architecture_globale.md)
Vue d'ensemble du système complet :
- Frontend React ↔ Backend FastAPI ↔ 3 Agents IA
- Flux de données séquentiels (5 flux détaillés)
- Technologies et stack
- Sécurité et déploiement

## 🎯 Vue d'ensemble rapide

```
┌─────────────┐
│   Frontend  │ React + Vite
│   React     │ TailwindCSS
└──────┬──────┘
       │ HTTPS + JWT
       ▼
┌─────────────┐
│   Backend   │ FastAPI
│   FastAPI   │ PostgreSQL
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Agent       │  │ Agent       │  │ Agent       │
│ Factures    │  │ Banque      │  │ Optimisation│
│             │  │             │  │             │
│ Gmail API   │  │ Excel       │  │ Analyse     │
│ PDF/OCR     │  │ Reader      │  │ Statistiques│
│ Groq LLM    │  │ Groq LLM    │  │ Groq LLM    │
└─────────────┘  └─────────────┘  └─────────────┘
```

## 🛠️ Technologies principales

### Frontend
- React 18+ avec Vite
- TailwindCSS + shadcn/ui
- Axios pour les appels API

### Backend
- FastAPI (Python)
- PostgreSQL avec SQLAlchemy
- JWT pour l'authentification
- Stockage fichiers local

### Agents IA
- **Groq API** : Analyse et rapprochement
- **Mistral Pixtral** : OCR sur images
- **Gmail API** : Récupération emails
- **pdfplumber** : Extraction PDF

## 📖 Comment utiliser cette documentation

1. **Commencer par l'architecture globale** pour comprendre le système dans son ensemble
2. **Consulter l'agent factures** pour comprendre le pipeline d'extraction
3. **Consulter l'agent banque** pour comprendre le rapprochement bancaire
4. **Consulter l'agent optimisation** pour comprendre l'analyse comptable globale

## 🔗 Liens rapides

- [Architecture Agent Banque](./architecture_agent_banque.md) - Rapprochement bancaire
- [Architecture Agent Factures](./architecture_agent_factures.md) - Extraction factures
- [Architecture Agent Optimisation](./architecture_agent_optimisation.md) - Analyse et optimisations
- [Architecture Globale](./architecture_globale.md) - Vue système complet

