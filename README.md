🌡️ BaillClim – Intégration BaillConnect pour Home Assistant (v3.0)



🔧 Description
BaillClim est une intégration personnalisée pour Home Assistant permettant de piloter votre climatiseur connecté via le portail BaillConnect.

Cette version v3.0 permet :

✅ Le changement de mode UC (Arrêt, Chauffage, Froid, Ventilation, etc.)

✅ La lecture des températures ambiantes des thermostats

✅ L’état ON/OFF des thermostats

⚠️ La gestion complète des thermostats (ex : modification des consignes de température) n’est pas encore disponible, mais est prévue dans une prochaine mise à jour.

🚀 Installation via HACS
1. Ajout du dépôt personnalisé
Ouvrez HACS → Intégrations → Menu (⋮) → Dépôts personnalisés

URL du dépôt : https://github.com/hebrru/baillclim

Catégorie : Intégration

Cliquez sur Ajouter

2. Installation
Installez l’intégration BaillClim

Redémarrez Home Assistant

Allez dans Paramètres → Appareils & Services → Ajouter une intégration

Recherchez BaillClim et entrez votre email + mot de passe

🛠️ Exemple d’automatisation
yaml
Copier
Modifier
alias: "Changer mode clim vers Ventilation"
trigger:
  - platform: time
    at: "12:00:00"
action:
  - service: select.select_option
    data:
      entity_id: select.mode_climatisation
      option: Ventilation
ℹ️ Remarques
🙈 Désolé si tout ne fonctionne pas parfaitement du premier coup :
C’est la première intégration que je développe et que je publie sur GitHub, donc il peut rester quelques ajustements à faire.

🧠 Je suis ouvert à vos retours et suggestions pour améliorer l’intégration !

📄 Licence
MIT – Libre de réutilisation, modification et intégration dans vos projets.

👤 Auteur
Développé par herbru
🔗 GitHub : hebrru/baillclim

