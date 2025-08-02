![HACS](https://img.shields.io/badge/HACS-gray?style=for-the-badge)
![CUSTOM](https://img.shields.io/badge/CUSTOM-blue?style=for-the-badge)
![RELEASE](https://img.shields.io/badge/RELEASE-green?style=for-the-badge)
![VERSION](https://img.shields.io/badge/V4.0.0-purple?style=for-the-badge)

# 🌡️ BaillClim – Intégration BaillConnect pour Home Assistant (v4.0.0)

**Publié par [@herbru](https://github.com/hebrru)**

---

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank"> <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" > </a>

---

## 🔧 Description

**BaillClim** est une intégration personnalisée pour **Home Assistant** permettant de piloter votre **climatiseur connecté via le portail BaillConnect**.

---

## 🆕 Nouveautés de la version 4.0.0

✅ Nouvelle détection **automatique des thermostats** via l’API  
✅ Retour d’état fiable sur le mode de climatisation (`select.mode_climatisation`)  
✅ Optimisation du polling avec `aiohttp`  
✅ Debug complet des données via `sensor.debug_baillconnect_data`  
✅ Ajout des entités `climate` :
- Simulation complète des thermostats BaillConnect
- Possibilité de les **mettre en `on` / `off`**
- Contrôle **direct de la température de consigne**

---

## 🚀 Installation via HACS

### 1. Ajouter le dépôt personnalisé

```txt
https://github.com/hebrru/baillclim
```

- Ouvrez HACS → Intégrations → Menu (⋮) → Dépôts personnalisés  
- Catégorie : **Intégration**  
- Cliquez sur **Ajouter**

### 2. Installation de l’intégration

- Installez **BaillClim** via HACS  
- Redémarrez Home Assistant  
- Allez dans **Paramètres → Appareils & Services → Ajouter une intégration**  
- Recherchez **BaillClim**  
- Entrez vos identifiants **BaillConnect** (email + mot de passe)

---

## ⚙️ Configuration manuelle obligatoire

### 1️⃣ Remplacer l’ID de régulation (`group_id`)

Dans le fichier `const.py`, remplacez les `XXX` par l’ID de votre installation, visible dans l’URL de BaillConnect :

```python
# custom_components/baillclim/const.py
REGULATIONS_URL = "https://www.baillconnect.com/client/regulations/XXX"
COMMAND_URL = "https://www.baillconnect.com/api-client/regulations/XXX"
```

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
```

---

## ℹ️ Remarques

🙈 Désolé si tout ne fonctionne pas parfaitement du premier coup.  
C’est ma première intégration Home Assistant, et aussi ma première publication GitHub.  
Mais je suis motivé pour continuer à l'améliorer 💪

---

## 🧠 Suggestions, bugs ou idées ?

👉 Ouvrez une issue ici : [GitHub Issues](https://github.com/hebrru/baillclim/issues)

---

## 📄 Licence

MIT – Libre de réutilisation, modification et intégration dans vos projets.

---

## 👤 Auteur

Développé par **herbru**  
🔗 GitHub : [hebrru/baillclim](https://github.com/hebrru/baillclim)

---

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
