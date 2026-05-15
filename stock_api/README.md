# API de Gestion des Ventes - Documentation

## 📋 Vue d'ensemble

Cette API gère les ventes dans un magasin qui vend des sacs de farines. Elle implémente trois rôles d'utilisateurs avec des permissions différentes :

### 👤 Rôles et Permissions

#### 1. **Worker (Travailleur)**
- ✅ Enregistrer les entrées et les ventes
- ✅ Créer des factures normalisées
- ✅ Voir son profil avec les activités et la dernière présence
- ✅ Protection contre le brute force (maximum 3 tentatives échouées = compte verrouillé)

#### 2. **Client (Manager)**
- ✅ Modifier les prix des produits
- ✅ Créer et gérer les réductions
- ✅ Voir le rapport hebdomadaire des ventes
- ✅ Consulter la moyenne de ventes
- ✅ Créer et supprimer des profils de workers
- ✅ Modifier les profils des workers
- ✅ Corriger les erreurs de ventes
- ✅ Visualiser les statistiques de ventes
- ✅ Voir le taux du jour

#### 3. **Super Admin**
- ✅ Accès à toutes les fonctionnalités
- ✅ Gestion complète du système

### 🔒 Sécurité

L'API est protégée contre :
- **Injection SQL** : Django utilise les paramètres liés par défaut
- **Brute Force** : Maximum 3 tentatives de connexion échouées (compte verrouillé pendant 15 minutes)
- **Abus d'API** : Limitation du débit (throttling) pour chaque endpoint
- **XSS** : Protection CSRF activée
- **Hashage des mots de passe** : Utilise PBKDF2 avec SHA256 (Argon2 disponible)

---

## 🚀 Installation et Configuration

### 1. Prérequis

```bash
python --version  # Python 3.8+
pip --version
```

### 2. Créer et Activer l'Environnement Virtuel

```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

**Fichier requirements.txt:**
```
Django==6.0.5
djangorestframework==3.17.1
django-cors-headers==4.0.0
```

### 4. Appliquer les Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Créer un Super Admin

```bash
python manage.py createsuperuser
# Suivre les instructions
```

### 6. Charger les Données de Test

```bash
python manage.py initialize_demo_data
```

Cela crée :
- 1 Super Admin (admin/admin123)
- 2 Workers (worker1/worker123, worker2/worker123)
- 2 Clients (client1/client123, client2/client123)
- 4 Produits de test
- Des réductions et des ventes de démonstration

### 7. Démarrer le Serveur

```bash
python manage.py runserver
```

L'API sera accessible sur : `http://localhost:8000/api/`

---

## 📚 Documentation des Endpoints

### 🔐 Authentification

#### 1. Enregistrement (Registration)

**Endpoint:** `POST /api/auth/register/`

**Données requises:**
```json
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password_123",
    "password_confirm": "secure_password_123",
    "role": "worker",  // "worker", "client", ou "super_admin"
    "first_name": "John",
    "last_name": "Doe"
}
```

**Réponse:**
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "worker",
    "token": "abc123xyz789",
    "message": "Utilisateur créé avec succès"
}
```

#### 2. Connexion (Login)

**Endpoint:** `POST /api/auth/login/`

**Données requises:**
```json
{
    "username": "john_doe",
    "password": "secure_password_123"
}
```

**Réponse:**
```json
{
    "token": "abc123xyz789",
    "user_id": 1,
    "username": "john_doe",
    "role": "worker",
    "message": "Connexion réussie"
}
```

**Protection Brute Force:**
- Maximum 5 tentatives par 15 minutes par adresse IP
- Après 3 tentatives échouées : compte verrouillé
- Seul un super admin peut déverrouiller

#### 3. Déconnexion (Logout)

**Endpoint:** `POST /api/auth/logout/`

**Authentification requise:** Oui (Token)

**Réponse:**
```json
{
    "message": "Déconnexion réussie"
}
```

---

### 👥 Gestion des Utilisateurs

#### 1. Lister les Utilisateurs

**Endpoint:** `GET /api/users/`

**Authentification requise:** Oui

**Permissions:**
- Super Admin : voit tous les utilisateurs
- Client : voit uniquement les workers
- Worker : voit uniquement son propre profil

**Réponse:**
```json
{
    "count": 10,
    "next": "http://localhost:8000/api/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "worker1",
            "email": "worker1@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "role": "worker"
        }
    ]
}
```

#### 2. Obtenir le Profil Personnel

**Endpoint:** `GET /api/users/me/`

**Authentification requise:** Oui

**Réponse:**
```json
{
    "id": 1,
    "username": "worker1",
    "email": "worker1@example.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "role": "worker",
    "last_presence": "10/05/2024 14:30:45",
    "last_presence_formatted": "10/05/2024 14:30:45",
    "activities_count": 15,
    "sales_count": 42,
    "is_locked": false
}
```

#### 3. Créer un Nouvel Utilisateur

**Endpoint:** `POST /api/users/`

**Authentification requise:** Oui

**Permissions:** Client ou Super Admin

**Données requises:**
```json
{
    "username": "new_worker",
    "email": "new@example.com",
    "password": "secure_pass123",
    "password_confirm": "secure_pass123",
    "role": "worker",
    "first_name": "Pierre",
    "last_name": "Martin"
}
```

#### 4. Déverrouiller un Compte

**Endpoint:** `POST /api/users/{user_id}/unlock_account/`

**Authentification requise:** Oui (Super Admin uniquement)

**Réponse:**
```json
{
    "message": "Compte de worker1 déverrouillé avec succès"
}
```

#### 5. Voir les Activités du Worker

**Endpoint:** `GET /api/users/activities/`

**Authentification requise:** Oui (Worker uniquement)

**Réponse:**
```json
[
    {
        "id": 1,
        "worker": 1,
        "worker_username": "worker1",
        "action": "login",
        "action_display": "Connexion",
        "description": "Connexion réussie",
        "timestamp": "2024-05-10T14:30:00Z",
        "ip_address": "192.168.1.1"
    }
]
```

---

### 📦 Gestion des Produits

#### 1. Lister les Produits

**Endpoint:** `GET /api/products/`

**Authentification requise:** Oui

**Paramètres de recherche:**
```
?search=Farine
?ordering=-created_at
```

**Réponse:**
```json
{
    "count": 4,
    "results": [
        {
            "id": 1,
            "name": "Farine de blé 10kg",
            "description": "Sac de farine de blé de 10 kilogrammes",
            "price": "15.99",
            "daily_price": "14.99",
            "current_price": "14.99",
            "quantity_in_stock": 95,
            "active_discount": {
                "id": 1,
                "percentage": "10",
                "description": "Réduction de 10% sur Farine de blé 10kg"
            },
            "created_at": "2024-05-01T10:00:00Z",
            "updated_at": "2024-05-10T10:00:00Z"
        }
    ]
}
```

#### 2. Voir les Produits en Stock Faible

**Endpoint:** `GET /api/products/low_stock/`

**Authentification requise:** Oui

**Réponse:** Liste des produits avec moins de 10 unités

#### 3. Modifier les Prix du Jour

**Endpoint:** `POST /api/products/update_daily_price/`

**Authentification requise:** Oui

**Permissions:** Client ou Super Admin

**Données requises:**
```json
{
    "products": [
        {
            "id": 1,
            "daily_price": 13.99
        },
        {
            "id": 2,
            "daily_price": 11.50
        }
    ]
}
```

**Réponse:** Liste des produits modifiés

---

### 🛒 Gestion des Ventes

#### 1. Créer une Vente

**Endpoint:** `POST /api/sales/`

**Authentification requise:** Oui

**Permissions:** Worker ou Super Admin

**Données requises:**
```json
{
    "product": 1,
    "quantity": 5,
    "discount": null  // ID de la réduction (optionnel)
}
```

**Réponse:**
```json
{
    "id": 1,
    "worker": 1,
    "worker_username": "worker1",
    "product": 1,
    "product_name": "Farine de blé 10kg",
    "quantity": 5,
    "unit_price": "14.99",
    "discount": null,
    "discount_percentage": null,
    "total_price": "74.95",
    "sale_date": "2024-05-10T14:35:00Z"
}
```

#### 2. Lister les Ventes d'Aujourd'hui

**Endpoint:** `GET /api/sales/today_sales/`

**Authentification requise:** Oui

**Réponse:** Liste des ventes du jour

#### 3. Statistiques des Ventes

**Endpoint:** `GET /api/sales/sales_statistics/`

**Authentification requise:** Oui

**Paramètres:**
```
?date_from=2024-05-01
?date_to=2024-05-10
```

**Réponse:**
```json
{
    "total_sales_count": 45,
    "total_sales_amount": "2345.67",
    "total_quantity_sold": 150,
    "average_sale_price": "52.13"
}
```

---

### 📄 Gestion des Factures

#### 1. Créer une Facture

**Endpoint:** `POST /api/invoices/`

**Authentification requise:** Oui

**Permissions:** Worker ou Super Admin

**Données requises:**
```json
{
    "sales": [1, 2, 3],  // IDs des ventes à inclure
    "notes": "Facture pour commande spéciale"
}
```

**Réponse:**
```json
{
    "id": 1,
    "invoice_number": "INV-20240510-ABC123",
    "worker": 1,
    "worker_name": "worker1",
    "sales": [...],
    "total_amount": "2345.67",
    "amount_paid": "0.00",
    "remaining_amount": "2345.67",
    "status": "draft",
    "status_display": "Brouillon",
    "notes": "Facture pour commande spéciale",
    "created_at": "2024-05-10T14:40:00Z",
    "issued_at": null
}
```

#### 2. Lister les Factures

**Endpoint:** `GET /api/invoices/`

**Authentification requise:** Oui

**Réponse:** Liste des factures

#### 3. Marquer une Facture comme Émise

**Endpoint:** `POST /api/invoices/{invoice_id}/mark_as_issued/`

**Authentification requise:** Oui

**Permissions:** Worker ou Super Admin

**Réponse:** Facture avec statut "issued"

#### 4. Marquer une Facture comme Payée

**Endpoint:** `POST /api/invoices/{invoice_id}/mark_as_paid/`

**Authentification requise:** Oui

**Permissions:** Client ou Super Admin

**Données requises (optionnel):**
```json
{
    "amount_paid": 2345.67  // Si non fourni = montant total
}
```

**Réponse:** Facture avec statut "paid"

---

### 🏷️ Gestion des Réductions

#### 1. Créer une Réduction

**Endpoint:** `POST /api/discounts/`

**Authentification requise:** Oui

**Permissions:** Client ou Super Admin

**Données requises:**
```json
{
    "product": 1,
    "discount_percentage": "15",
    "start_date": "2024-05-01T00:00:00Z",
    "end_date": "2024-05-31T23:59:59Z",
    "description": "Promotion spéciale mai"
}
```

**Réponse:**
```json
{
    "id": 1,
    "product": 1,
    "discount_percentage": "15",
    "start_date": "2024-05-01T00:00:00Z",
    "end_date": "2024-05-31T23:59:59Z",
    "description": "Promotion spéciale mai",
    "is_active": true,
    "created_at": "2024-05-10T10:00:00Z"
}
```

#### 2. Lister les Réductions Actives

**Endpoint:** `GET /api/discounts/active_discounts/`

**Authentification requise:** Oui

**Réponse:** Liste des réductions actuellement actives

---

### 📊 Rapports et Statistiques

#### 1. Rapport Hebdomadaire

**Endpoint:** `GET /api/reports/weekly/`

**Authentification requise:** Oui

**Permissions:** Client ou Super Admin

**Réponse:**
```json
{
    "week_start": "2024-05-06",
    "week_end": "2024-05-12",
    "total_sales": "5432.10",
    "total_quantity": 250,
    "average_daily_sales": "775.44",
    "daily_breakdown": [
        {
            "report_date": "2024-05-06",
            "total_sales_count": 35,
            "total_sales_amount": "1234.56",
            "total_quantity_sold": 40,
            "average_sale_price": "35.27"
        }
    ]
}
```

#### 2. Moyenne de Ventes

**Endpoint:** `GET /api/reports/average-sales/`

**Authentification requise:** Oui

**Permissions:** Client ou Super Admin

**Réponse:**
```json
{
    "period": "7 derniers jours",
    "total_sales": "5432.10",
    "total_sales_count": 150,
    "average_sale_price": "36.21",
    "average_sales_per_day": "775.44"
}
```

#### 3. Rapports Journaliers

**Endpoint:** `GET /api/reports/daily/`

**Authentification requise:** Oui

**Permissions:** Client ou Super Admin

**Réponse:** Liste des rapports journaliers

---

## 🔄 Flux d'Utilisation Typique

### Pour un Worker

1. **Connexion**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"worker1","password":"worker123"}'
   ```

2. **Enregistrer une Vente**
   ```bash
   curl -X POST http://localhost:8000/api/sales/ \
     -H "Authorization: Token abc123xyz789" \
     -H "Content-Type: application/json" \
     -d '{"product":1,"quantity":5}'
   ```

3. **Voir ses Activités**
   ```bash
   curl -X GET http://localhost:8000/api/users/activities/ \
     -H "Authorization: Token abc123xyz789"
   ```

4. **Créer une Facture**
   ```bash
   curl -X POST http://localhost:8000/api/invoices/ \
     -H "Authorization: Token abc123xyz789" \
     -H "Content-Type: application/json" \
     -d '{"sales":[1,2,3],"notes":"Facture du jour"}'
   ```

### Pour un Client

1. **Connexion**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"client1","password":"client123"}'
   ```

2. **Modifier le Prix du Jour**
   ```bash
   curl -X POST http://localhost:8000/api/products/update_daily_price/ \
     -H "Authorization: Token token789xyz" \
     -H "Content-Type: application/json" \
     -d '{"products":[{"id":1,"daily_price":13.99}]}'
   ```

3. **Créer une Réduction**
   ```bash
   curl -X POST http://localhost:8000/api/discounts/ \
     -H "Authorization: Token token789xyz" \
     -H "Content-Type: application/json" \
     -d '{
       "product":1,
       "discount_percentage":"20",
       "start_date":"2024-05-10T00:00:00Z",
       "end_date":"2024-05-20T23:59:59Z",
       "description":"Solde printemps"
     }'
   ```

4. **Voir le Rapport Hebdomadaire**
   ```bash
   curl -X GET http://localhost:8000/api/reports/weekly/ \
     -H "Authorization: Token token789xyz"
   ```

---

## 🛡️ Éléments de Sécurité Implémentés

### 1. **Authentification**
- Token d'authentification personnalisé
- Mots de passe hashés avec PBKDF2
- Sessions sécurisées

### 2. **Autorisation**
- Permissions basées sur les rôles (RBAC)
- Contrôle d'accès granulaire par endpoint

### 3. **Protection contre le Brute Force**
- Maximum 3 tentatives de connexion échouées
- Compte verrouillé pendant 15 minutes
- Tracking de l'adresse IP

### 4. **Protection contre l'Injection SQL**
- Utilisation des paramètres liés de Django ORM
- Validation et sanitisation des entrées

### 5. **Limitation de Débit (Throttling)**
- 10 requêtes/minute pour les utilisateurs authentifiés
- 5 requêtes/minute pour les utilisateurs anonymes
- Limites spéciales pour les endpoints critiques

### 6. **Sécurité HTTP**
- CSRF Protection activée
- XSS Filter activé
- Content Security Policy configurée

---

## 📝 Codes de Statut HTTP

| Code | Signification |
|------|---------------|
| 200 | OK - Requête réussie |
| 201 | Created - Ressource créée |
| 400 | Bad Request - Données invalides |
| 401 | Unauthorized - Non authentifié |
| 403 | Forbidden - Permission refusée |
| 404 | Not Found - Ressource non trouvée |
| 429 | Too Many Requests - Limite de débit dépassée |
| 500 | Internal Server Error - Erreur serveur |

---

## 🚨 Gestion des Erreurs

L'API retourne les erreurs au format JSON :

```json
{
    "error": "Message d'erreur descriptif",
    "details": {
        "field": ["Erreur spécifique"]
    }
}
```

---

## 📞 Support et Maintenance

Pour des informations supplémentaires ou un support :
- Consulter la documentation Django : https://docs.djangoproject.com
- Consulter la documentation DRF : https://www.django-rest-framework.org
- Vérifier les logs dans `logs/error.log`

---

**Dernière mise à jour:** 10 mai 2024
