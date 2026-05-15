# 📖 Guide d'Installation - API Stock Management

## ✅ Prérequis

Avant de commencer, assurez-vous que vous avez :

- **Python 3.8+** installé
- **pip** (Python Package Manager)
- **Git** (optionnel)
- Un terminal/console (PowerShell, CMD, Terminal, etc.)

Vérifiez l'installation :

```bash
python --version
pip --version
```

---

## 🔧 Étape 1 : Cloner ou Télécharger le Projet

### Option A : Cloner depuis Git

```bash
git clone <url-du-repo>
cd stock_api
```

### Option B : Utiliser les fichiers existants

Naviguez vers le dossier du projet :

```bash
cd c:\Users\MATHIEU\Desktop\stock_api\stock_api
```

---

## 🐍 Étape 2 : Créer l'Environnement Virtuel

### Windows (PowerShell)

```powershell
python -m venv env
env\Scripts\Activate.ps1
```

### Windows (CMD)

```cmd
python -m venv env
env\Scripts\activate.bat
```

### Linux/Mac

```bash
python3 -m venv env
source env/bin/activate
```

**Vous devriez voir `(env)` au début de votre prompt.**

---

## 📦 Étape 3 : Installer les Dépendances

```bash
pip install -r requirements.txt
```

**Dépendances installées:**
- Django 6.0.5
- Django REST Framework 3.17.1
- Django CORS Headers 4.0.0
- Django Filter 24.1

---

## ⚙️ Étape 4 : Configuration

### 4.1 Créer le fichier .env (Optionnel)

```bash
# Copier le fichier d'exemple
cp .env.example .env  # Linux/Mac
copy .env.example .env  # Windows
```

Puis modifier `.env` selon vos besoins.

### 4.2 Créer la Base de Données et Appliquer les Migrations

```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate
```

Vous devriez voir :

```
Operations to perform:
  Apply all migrations: admin, auth, authtoken, contenttypes, sales, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
```

---

## 👤 Étape 5 : Créer un Super Admin

```bash
python manage.py createsuperuser
```

Suivez les instructions :

```
Username: admin
Email address: admin@example.com
Password: 
Password (again):
Superuser created successfully.
```

---

## 📊 Étape 6 : Charger les Données de Test (Optionnel)

```bash
python manage.py initialize_demo_data
```

Cela crée :

✅ **1 Super Admin**
- Username: `admin`
- Password: `admin123`

✅ **2 Workers**
- Username: `worker1` / `worker2`
- Password: `worker123`

✅ **2 Clients**
- Username: `client1` / `client2`
- Password: `client123`

✅ **4 Produits** (Sacs de farines)

✅ **Réductions et Ventes** de démonstration

---

## 🚀 Étape 7 : Démarrer le Serveur

```bash
python manage.py runserver
```

Vous verrez :

```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

---

## 🌐 Accéder à l'API

### URL Principale

- **API Root:** http://localhost:8000/api/
- **Admin Interface:** http://localhost:8000/admin/

### Exemple de Connexion

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "worker1",
    "password": "worker123"
  }'
```

Réponse :

```json
{
    "token": "abc123xyz789def456",
    "user_id": 2,
    "username": "worker1",
    "role": "worker",
    "message": "Connexion réussie"
}
```

Utilisez ce token pour accéder aux endpoints protégés :

```bash
curl -H "Authorization: Token abc123xyz789def456" \
  http://localhost:8000/api/users/me/
```

---

## 📁 Structure du Projet

```
stock_api/
├── env/                          # Environnement virtuel
├── stock_api/                    # Configuration Django
│   ├── __init__.py
│   ├── settings.py              # ⚙️ Configuration principale
│   ├── urls.py                  # 🔗 Routes principales
│   ├── wsgi.py
│   └── asgi.py
├── sales/                        # Application API
│   ├── migrations/              # Migrations de base de données
│   ├── management/
│   │   └── commands/
│   │       └── initialize_demo_data.py  # 📊 Données de test
│   ├── models.py                # 📦 Modèles de données
│   ├── views.py                 # 👁️  Logique des endpoints
│   ├── serializers.py           # 🔄 Sérialisation JSON
│   ├── urls.py                  # 🔗 Routes API
│   ├── permissions.py           # 🔒 Permissions
│   ├── throttling.py            # ⏱️  Limitation de débit
│   ├── admin.py                 # 🖥️  Interface admin
│   ├── apps.py
│   └── tests.py                 # 🧪 Tests unitaires
├── manage.py                     # Outil de gestion Django
├── requirements.txt              # 📦 Dépendances
├── README.md                     # 📖 Documentation
├── .env.example                  # 📋 Variables d'environnement
├── db.sqlite3                    # 💾 Base de données
└── logs/                         # 📝 Fichiers de log
    └── error.log
```

---

## 🔍 Tests

### Exécuter les Tests

```bash
python manage.py test sales
```

### Exécuter un Test Spécifique

```bash
python manage.py test sales.tests.UserAuthenticationTests
```

---

## 🐛 Dépannage

### Problème : "ModuleNotFoundError: No module named 'sales'"

**Solution:**
```bash
# Assurez-vous que vous êtes dans le dossier du projet
cd c:\Users\MATHIEU\Desktop\stock_api\stock_api

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Problème : "Port 8000 already in use"

**Solution:**
```bash
# Utiliser un autre port
python manage.py runserver 8001
```

### Problème : "Database lock"

**Solution:**
```bash
# Supprimer la base de données
rm db.sqlite3  # Linux/Mac
del db.sqlite3  # Windows

# Recréer la base de données
python manage.py migrate
```

### Problème : "Static files not found"

**Solution:**
```bash
# Collecter les fichiers statiques
python manage.py collectstatic
```

---

## 📚 Ressources Utiles

- **Documentation Django:** https://docs.djangoproject.com
- **Django REST Framework:** https://www.django-rest-framework.org
- **API Documentation:** Voir `README.md`

---

## ⚡ Quick Commands Reference

```bash
# Activer l'environnement
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# Désactiver l'environnement
deactivate

# Démarrer le serveur
python manage.py runserver

# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Accéder à la console Django
python manage.py shell

# Créer un superuser
python manage.py createsuperuser

# Charger les données de test
python manage.py initialize_demo_data

# Exécuter les tests
python manage.py test sales

# Collecter les fichiers statiques
python manage.py collectstatic
```

---

## ✨ Prochaines Étapes

1. ✅ Parcourir la documentation complète dans `README.md`
2. ✅ Tester les endpoints avec Postman ou cURL
3. ✅ Créer des utilisateurs supplémentaires
4. ✅ Enregistrer des ventes
5. ✅ Générer des rapports

---

**Besoin d'aide?** Consultez la documentation complète dans `README.md` ou vérifiez les logs d'erreur.

**Bonne utilisation de l'API! 🚀**
