![HACS](https://img.shields.io/badge/HACS-gray?style=for-the-badge)
![CUSTOM](https://img.shields.io/badge/CUSTOM-blue?style=for-the-badge)
![RELEASE](https://img.shields.io/badge/RELEASE-gray?style=for-the-badge)
![VERSION](https://img.shields.io/badge/V3.0.0-blue?style=for-the-badge)

# 🌡️ BaillClim – Intégration BaillConnect pour Home Assistant (v3.0)

**Publié par [@herbru](https://github.com/hebrru)**

---

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank"> <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" > </a> ```


## 🔧 Description

**BaillClim** est une intégration personnalisée pour **Home Assistant** permettant de piloter votre **climatiseur connecté via le portail [BaillConnect](https://www.baillconnect.com)**.

---

## 🆕 Nouveautés de la version 3.0

✅ **Changement de mode UC** (Arrêt, Chauffage, Froid, Ventilation, etc.)  
✅ **Lecture des températures ambiantes** de chaque thermostat  
✅ **État ON/OFF des thermostats** (lecture uniquement)  

> ⚠️ Le **pilotage des températures de consigne** n’est pas encore disponible. Il est prévu dans une future mise à jour.

---

## 🚀 Installation via HACS

### 1. Ajouter le dépôt personnalisé

https://github.com/hebrru/baillclim

yaml
Copier
Modifier

- Ouvrez **HACS → Intégrations → Menu (⋮) → Dépôts personnalisés**
- Catégorie : **Intégration**
- Cliquez sur **Ajouter**

### 2. Installation de l’intégration

- Installez **BaillClim** via HACS
- Redémarrez Home Assistant
- Allez dans **Paramètres → Appareils & Services → Ajouter une intégration**
- Recherchez **BaillClim**
- Entrez vos **identifiants BaillConnect** (email + mot de passe)

---

## 🛠️ Exemple d’automatisation YAML

```yaml
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
C’est ma première intégration Home Assistant, et aussi la première fois que je publie sur GitHub. J’ai encore des progrès à faire, mais je suis très motivé !

🧠 Suggestions, bugs ou idées d’amélioration ?
Vos retours sont les bienvenus ! Ouvrez une issue ici 👉 Issues GitHub

📄 Licence
MIT – Libre de réutilisation, modification et intégration dans vos projets.

👤 Auteur
Développé par herbru
🔗 GitHub : hebrru/baillclim

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank"> <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" > </a> ```