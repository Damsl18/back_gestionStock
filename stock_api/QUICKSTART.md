# 🚀 Démarrage Rapide - Stock API

## ⚡ En 5 minutes

### 1. Activer l'Environnement Virtuel

```bash
# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

### 2. Appliquer les Migrations

```bash
python manage.py migrate
```

### 3. Charger les Données de Test

```bash
python manage.py initialize_demo_data
```

### 4. Démarrer le Serveur

```bash
python manage.py runserver
```

### 5. Tester l'API

**Option A : Postman (Recommandé)**

1. Télécharger et installer [Postman](https://www.postman.com/downloads/)
2. Importer le fichier `Stock_API_Postman.json`
3. Utiliser les exemples de requêtes fournis

**Option B : cURL**

```bash
# Connexion
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"worker1","password":"worker123"}'

# Copier le token retourné et l'utiliser pour les requêtes suivantes
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

**Option C : Interface Web**

1. Aller à http://localhost:8000/admin
2. Connexion avec : admin/admin123
3. Ou aller à http://localhost:8000/api pour voir tous les endpoints

---

## 📚 Utilisateurs de Test

| Role | Username | Password | Accès |
|------|----------|----------|-------|
| Super Admin | `admin` | `admin123` | Tous les endpoints |
| Worker | `worker1` | `worker123` | Ventes, Factures |
| Worker | `worker2` | `worker123` | Ventes, Factures |
| Client | `client1` | `client123` | Rapports, Réductions, Prix |
| Client | `client2` | `client123` | Rapports, Réductions, Prix |

---

## 🔗 URLs Principales

| URL | Description |
|-----|-------------|
| http://localhost:8000/admin | Interface d'administration Django |
| http://localhost:8000/api | Racine de l'API |
| http://localhost:8000/api/auth/login | Connexion |
| http://localhost:8000/api/auth/register | Enregistrement |
| http://localhost:8000/api/users | Gestion des utilisateurs |
| http://localhost:8000/api/products | Gestion des produits |
| http://localhost:8000/api/sales | Enregistrement des ventes |
| http://localhost:8000/api/invoices | Gestion des factures |
| http://localhost:8000/api/discounts | Gestion des réductions |
| http://localhost:8000/api/reports/weekly | Rapport hebdomadaire |

---

## 🎯 Exemples de Flux

### Flux Worker - Enregistrer une Vente

```bash
# 1. Connexion
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"worker1","password":"worker123"}' | grep -o '"token":"[^"]*' | cut -d'"' -f4)

# 2. Enregistrer une vente
curl -X POST http://localhost:8000/api/sales/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product":1,"quantity":5}'

# 3. Créer une facture
curl -X POST http://localhost:8000/api/invoices/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sales":[1],"notes":"Vente du jour"}'
```

### Flux Client - Voir les Rapports

```bash
# 1. Connexion
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"client1","password":"client123"}' | grep -o '"token":"[^"]*' | cut -d'"' -f4)

# 2. Voir le rapport hebdomadaire
curl -X GET http://localhost:8000/api/reports/weekly/ \
  -H "Authorization: Token $TOKEN"

# 3. Voir la moyenne de ventes
curl -X GET http://localhost:8000/api/reports/average-sales/ \
  -H "Authorization: Token $TOKEN"
```

---

## 📁 Structure des Fichiers Importants

```
stock_api/
├── INSTALL.md              # Guide complet d'installation
├── README.md               # Documentation complète
├── QUICKSTART.md           # Ce fichier
├── requirements.txt        # Dépendances Python
├── Stock_API_Postman.json  # Collection Postman
├── manage.py               # Outil de gestion Django
├── db.sqlite3              # Base de données
└── sales/                  # Application API
    ├── models.py           # Modèles de données
    ├── views.py            # Endpoints API
    ├── serializers.py      # Conversion JSON
    ├── permissions.py      # Contrôle d'accès
    └── throttling.py       # Limitation de débit
```

---

## 🔧 Commandes Utiles

```bash
# Voir toutes les ventes
python manage.py dbshell << 'EOF'
SELECT * FROM sales_sale;
EOF

# Voir tous les utilisateurs
python manage.py shell << 'EOF'
from sales.models import CustomUser
for user in CustomUser.objects.all():
    print(f"{user.username} - {user.role}")
EOF

# Créer une sauvegarde
python manage.py dumpdata > backup.json

# Restaurer à partir d'une sauvegarde
python manage.py loaddata backup.json
```

---

## 🆘 Problèmes Courants

**Problème:** Port 8000 déjà utilisé
```bash
python manage.py runserver 8001
```

**Problème:** "No such table: sales_customuser"
```bash
python manage.py migrate
```

**Problème:** "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

---

## 📖 Documentation Complète

Voir les fichiers :
- **INSTALL.md** - Installation détaillée
- **README.md** - Documentation complète des endpoints

---

## 🎓 Prochaines Étapes

1. ✅ Tester les endpoints avec Postman
2. ✅ Créer des ventes de test
3. ✅ Consulter les rapports
4. ✅ Créer des réductions
5. ✅ Lire la documentation complète

---

**Besoin d'aide?**
- Consultez README.md pour la documentation complète
- Vérifiez les logs si vous avez une erreur
- Utilisez Postman pour tester les requêtes

**Bon développement! 🚀**
