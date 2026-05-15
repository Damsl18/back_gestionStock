# 🏗️ Architecture et Conception de l'API

## 📐 Diagramme Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT (Frontend/Postman)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/HTTPS
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    Django REST Framework                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             URL Routing (urls.py)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │      Authentification & Autorisation                     │   │
│  │  - Token d'authentification                              │   │
│  │  - Permissions basées sur les rôles (RBAC)              │   │
│  │  - Throttling/Rate Limiting                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Views (viewsets.py)                             │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ UserViewSet | ProductViewSet | SaleViewSet | ... │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │       Serializers (serializers.py)                       │   │
│  │  - Validation des données                               │   │
│  │  - Sérialisation/Désérialisation JSON                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           ORM Django (models.py)                         │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ CustomUser | Product | Sale | Invoice | ... │     │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   Base de Données (SQLite)                      │
│                    (db.sqlite3)                                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 👥 Modèle de Données (Data Model)

### Entités Principales

```
┌────────────────────┐
│   CustomUser       │
├────────────────────┤
│ id (PK)            │
│ username (Unique)  │
│ email              │
│ password (Hashed)  │
│ role (FK)          │◄──────────┐
│ failed_attempts    │           │
│ is_locked          │     ┌─────┴────────────────┐
│ last_presence      │     │                      │
│ created_at         │     │  ROLE_CHOICES       │
│ updated_at         │     │  - worker            │
└────────────────────┘     │  - client            │
        │ 1                │  - super_admin       │
        │ * Activity       │                      │
        │ * Sale           │                      │
        │ * Invoice        │                      │
        └                  └──────────────────────┘
        
┌────────────────────┐
│    Product         │
├────────────────────┤
│ id (PK)            │
│ name (Unique)      │
│ description        │
│ price              │
│ daily_price        │
│ quantity_in_stock  │
│ created_at         │
│ updated_at         │
└────────────────────┘
        │ 1
        │ * Sale
        │ * Discount
        │
        
┌────────────────────┐
│   Sale             │
├────────────────────┤
│ id (PK)            │
│ worker_id (FK)     │──────────► CustomUser
│ product_id (FK)    │──────────► Product
│ quantity           │
│ unit_price         │
│ total_price        │
│ discount_id (FK)   │──────────► Discount (nullable)
│ sale_date          │
└────────────────────┘
        │ *
        │ Many-to-Many
        │ * Invoice
        │
        
┌────────────────────┐
│   Invoice          │
├────────────────────┤
│ id (PK)            │
│ invoice_number     │
│ worker_id (FK)     │──────────► CustomUser
│ sales[] (M2M)      │──────────► Sale
│ total_amount       │
│ amount_paid        │
│ status             │
│ notes              │
│ created_at         │
│ issued_at          │
└────────────────────┘

┌────────────────────┐
│   Discount         │
├────────────────────┤
│ id (PK)            │
│ product_id (FK)    │──────────► Product
│ discount_percent   │
│ start_date         │
│ end_date           │
│ description        │
│ created_at         │
└────────────────────┘

┌────────────────────┐
│  ActivityLog       │
├────────────────────┤
│ id (PK)            │
│ worker_id (FK)     │──────────► CustomUser
│ action             │
│ description        │
│ timestamp          │
│ ip_address         │
└────────────────────┘

┌────────────────────┐
│  DailyReport       │
├────────────────────┤
│ id (PK)            │
│ report_date        │
│ total_sales_count  │
│ total_sales_amount │
│ total_qty_sold     │
│ average_price      │
│ created_at         │
└────────────────────┘
```

---

## 🔐 Couches de Sécurité

### 1. **Authentification (Authentication)**

```
┌──────────────────────────────────────┐
│    Client (API Request)              │
└──────────────────────────────────────┘
              │
              │ Username + Password
              ▼
┌──────────────────────────────────────┐
│    User Login View                   │
│  - Vérifier Username/Password        │
│  - Compter tentatives échouées       │
│  - Verrouiller après 3 tentatives   │
└──────────────────────────────────────┘
              │
              │ Succès
              ▼
┌──────────────────────────────────────┐
│    Token Generation                  │
│  - Créer Token d'authentification   │
│  - Sauvegarder IP du client          │
│  - Enregistrer l'activité            │
└──────────────────────────────────────┘
              │
              │ Token
              ▼
┌──────────────────────────────────────┐
│    Client Stocke Token               │
│    - Headers: Authorization: Token   │
└──────────────────────────────────────┘
```

### 2. **Autorisation (Authorization)**

```
┌──────────────────────────────────────────┐
│    Requête API Entrante                  │
└──────────────────────────────────────────┘
              │
              │ Vérifie Token
              ▼
┌──────────────────────────────────────────┐
│    Authentification OK?                  │
│    - Token valide?                       │
│    - Utilisateur existe?                 │
└──────────────────────────────────────────┘
              │
     ┌────────┴────────┐
     │                 │
    OUI               NON
     │                 │
     ▼                 ▼
┌─────────────┐   ┌──────────────┐
│ Vérifier    │   │ 401          │
│ Permissions │   │ Unauthorized │
│ du Rôle     │   └──────────────┘
└─────────────┘
     │
┌────┴────────────────────────────┐
│ Rôle = Worker?                  │
│ Rôle = Client?                  │
│ Rôle = Super Admin?             │
└────┬────────────────────────────┘
     │
┌────┴──────────────────────────┐
│ Vérifier Permissions Endpoint  │
│ - IsWorker                     │
│ - IsClient                     │
│ - IsSuperAdmin                 │
│ - IsClientOrSuperAdmin         │
└────┬──────────────────────────┘
     │
    ✓/✗
     │
   OUI/NON
```

### 3. **Protection contre le Brute Force**

```
┌─────────────────────────────────┐
│    Tentative de Connexion       │
└─────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────┐
│  Vérifier IP                    │
│  - Nombre de tentatives?        │
│  - Temps écoulé depuis?         │
└─────────────────────────────────┘
              │
     ┌────────┴────────┐
     │                 │
  <3 tentatives    ≥3 tentatives
     │                 │
     ▼                 ▼
┌──────────┐       ┌──────────────┐
│ OK       │       │ BLOQUÉ       │
│ Vérifier │       │ Pour 15 min  │
│ Crédents │       └──────────────┘
└──────────┘
     │
     ├─ Incorrect: failed_attempts++
     │
     └─ Correct: failed_attempts=0
```

### 4. **Protection contre l'Injection SQL**

```
┌──────────────────────────────────────┐
│    Requête SQL Malveillante          │
│    SELECT * FROM user WHERE          │
│    username = 'admin'; DROP TABLE;' │
└──────────────────────────────────────┘
              │
              │ Django ORM
              ▼
┌──────────────────────────────────────┐
│    Parameterized Query (Prepared)    │
│    SELECT * FROM user WHERE          │
│    username = ?                      │
│    Parameters: ['admin']             │
└──────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│    Exécution Sécurisée               │
│    - Les paramètres sont échappés    │
│    - Pas d'interprétation SQL       │
│    - Protection garantie             │
└──────────────────────────────────────┘
```

### 5. **Throttling (Limitation de Débit)**

```
┌─────────────────────────────────┐
│    Requête API                  │
└─────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  Obtenir clé de Cache               │
│  - Token utilisateur OU              │
│  - Adresse IP                        │
└──────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────┐
│  Vérifier Limite de Débit            │
│  - Requêtes: 10 par minute           │
│  - Utilisateur auth: 100 par heure   │
│  - Anonyme: 5 par minute             │
└──────────────────────────────────────┘
              │
     ┌────────┴────────┐
     │                 │
  DANS LIMITE      HORS LIMITE
     │                 │
     ▼                 ▼
┌──────────┐       ┌──────────┐
│ Accepter │       │ 429      │
│ Requête  │       │ Too Many │
└──────────┘       │ Requests │
                   └──────────┘
```

---

## 🔄 Flux de Données Exemple

### Flux Complet: Worker Enregistre une Vente

```
1. LOGIN
   POST /api/auth/login/
   Body: {username, password}
   ↓
   Response: {token, user_id, role}

2. ENREGISTRER VENTE
   POST /api/sales/
   Header: Authorization: Token {token}
   Body: {product_id, quantity}
   ↓
   - Vérifier Token → OK
   - Vérifier Permissions → IsWorker → OK
   - Vérifier Throttle → 10/min → OK
   - Vérifier Stock → quantity_in_stock
   - Créer Sale
   - Réduire Stock
   - Enregistrer ActivityLog
   ↓
   Response: {id, product_name, quantity, total_price}

3. CRÉER FACTURE
   POST /api/invoices/
   Header: Authorization: Token {token}
   Body: {sales: [1, 2, 3], notes}
   ↓
   - Vérifier Token → OK
   - Vérifier Permissions → IsWorker → OK
   - Vérifier Throttle → OK
   - Générer invoice_number
   - Créer Invoice
   - Calculer total_amount
   - Enregistrer ActivityLog
   ↓
   Response: {invoice_number, total_amount, status}
```

---

## 📊 Limitations et Throttling

| Endpoint | Rôle | Limite | Période |
|----------|------|--------|---------|
| Login | Tous | 5 | 15 min |
| Register | Tous | 10 | 1 heure |
| Ventes | Worker | 500 | 1 heure |
| Prix | Client | 50 | 1 heure |
| Réductions | Client | 30 | 1 heure |
| Normal | Authentifié | 10 | 1 minute |
| Normal | Anonyme | 5 | 1 minute |

---

## 🛣️ Routing et Endpoints

```
/api/
├── auth/
│   ├── register/        POST   (Public)
│   ├── login/          POST   (Public)
│   └── logout/         POST   (Authentifié)
│
├── users/
│   ├── /                GET    (Authentifié)
│   ├── {id}/           GET    (Authentifié)
│   ├── me/             GET    (Authentifié)
│   ├── activities/     GET    (Worker)
│   └── {id}/unlock/    POST   (SuperAdmin)
│
├── products/
│   ├── /                GET    (Authentifié)
│   ├── {id}/           GET    (Authentifié)
│   ├── /                POST   (Client/Admin)
│   ├── low_stock/      GET    (Authentifié)
│   └── update_daily_price/ POST (Client/Admin)
│
├── sales/
│   ├── /                GET    (Authentifié)
│   ├── /                POST   (Worker/Admin)
│   ├── today_sales/    GET    (Authentifié)
│   └── statistics/     GET    (Authentifié)
│
├── invoices/
│   ├── /                GET    (Authentifié)
│   ├── {id}/           GET    (Authentifié)
│   ├── /                POST   (Worker/Admin)
│   ├── {id}/mark_as_issued/   POST   (Worker/Admin)
│   └── {id}/mark_as_paid/     POST   (Client/Admin)
│
├── discounts/
│   ├── /                GET    (Authentifié)
│   ├── {id}/           GET    (Authentifié)
│   ├── /                POST   (Client/Admin)
│   └── active_discounts/ GET  (Authentifié)
│
└── reports/
    ├── daily/          GET    (Client/Admin)
    ├── weekly/         GET    (Client/Admin)
    └── average-sales/  GET    (Client/Admin)
```

---

## 🏆 Principes de Conception

### 1. **DRY (Don't Repeat Yourself)**
- Sérialiseurs réutilisables
- Permissions partagées
- ViewSets génériques

### 2. **SOLID Principles**
- Single Responsibility: Chaque classe a une responsabilité
- Open/Closed: Extensible sans modification
- Interface Segregation: Permissions granulaires
- Dependency Inversion: Utilisation de l'injection
- Liskov Substitution: Héritage correct

### 3. **Security First**
- Validation des entrées
- Authentification obligatoire
- Autorisations granulaires
- Throttling des abus
- Logging de sécurité

### 4. **REST Conventions**
- Utilisation correcte des verbes HTTP
- Codes de statut appropriés
- Nommage cohérent des endpoints
- Versionnement (prévu)

---

## 📈 Scalabilité Future

### Optimisations Possibles

1. **Database**
   - Utiliser PostgreSQL en production
   - Ajouter des indexes
   - Partitionnement des tables volumineuses

2. **Caching**
   - Redis pour les sessions
   - Cache des rapports
   - ETag pour les réponses

3. **API**
   - Versionnement (v1/, v2/)
   - GraphQL (alternative)
   - Webhooks

4. **Infrastructure**
   - Docker containerization
   - Kubernetes orchestration
   - Load balancing
   - CDN

---

**Architecture conçue pour la croissance et la sécurité!** 🚀
