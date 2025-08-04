🌡️ BaillClim – Intégration BaillConnect pour Home Assistant
HACS CUSTOM RELEASE
Développé par @hebrru
☕ Buy Me A Coffee

🔧 Description
BaillClim est une intégration personnalisée pour Home Assistant, permettant de piloter vos thermostats connectés via le portail baillconnect.com. Elle offre un contrôle complet de votre système de climatisation gainable, pièce par pièce, zone par zone, et prend en charge plusieurs passerelles ou régulations.

🧩 Entités disponibles
L’intégration crée automatiquement les entités suivantes en fonction des données disponibles dans votre compte :

🔥 climate.baillclim_*
Thermostats BaillConnect avec les fonctionnalités :

🟢 Allumage/extinction

🌡️ Température ambiante

❄️ Consigne froide (gauche)

🔥 Consigne chaude (droite)

🔄 Mode AUTO ou OFF (dépend de l’état réel)

🌀 select.mode_climatisation
Contrôle du mode général de fonctionnement du système :

Arrêt, Froid, Chauffage, Désumidificateur, Ventilation

🌡️ sensor.baillclim_temp_*
Capteurs de température ambiante pour chaque thermostat, lisibles séparément.

💡 switch.zone_*_active
Permet d’activer ou désactiver une zone programmée :

Positionne la zone en mode actif (mode: 3) ou inactif (mode: 0)

🐞 sensor.debug_baillconnect_data
Capteur spécial contenant l'intégralité des données JSON brutes retournées par l'API :

Très utile pour le debug, ou pour les utilisateurs avancés souhaitant extraire d'autres données.

🧠 Points forts
✅ Détection automatique des thermostats, zones et régulations
✅ Aucune configuration manuelle des ID
✅ Prise en charge de plusieurs régulations sur le même compte
✅ Préparation pour un multi-compte / multi-passerelle
✅ Entièrement compatible Lovelace
✅ Fonctionne sans dépendance cloud tierce, uniquement via le site BaillConnect

🚀 Installation via HACS
Ajouter ce dépôt personnalisé :

arduino
Copier
Modifier
https://github.com/hebrru/baillclim
Dans HACS :

HACS → Intégrations → (⋮) → Dépôts personnalisés

Catégorie : Intégration

Installer BaillClim

Redémarrer Home Assistant

Aller dans :
Paramètres → Appareils & Services → Ajouter une intégration

Rechercher BaillClim

Entrer votre email et mot de passe BaillConnect

🛠️ Exemple d’automatisation YAML
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
🧠 Suggestions / Bugs / Améliorations
👉 Créez une issue GitHub pour proposer une idée ou signaler un problème.

👤 Auteur
Hervé G.
GitHub : hebrru
☕ Buy Me A Coffee