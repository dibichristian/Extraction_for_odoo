# Étape 1 : Utiliser une image de base Python
FROM python:3.11-slim

# Étape 2 : Définir le répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Étape 3 : Copier les fichiers nécessaires dans le conteneur
COPY requirements.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install -r requirements.txt

# Copier tout le contenu, sauf les éléments exclus dans .dockerignore
COPY . /app

# Étape 4 : Exposer le port pour l'application Flask
EXPOSE 5000

# Étape 5 : Définir la commande pour exécuter votre application
CMD ["python", "app.py"]
