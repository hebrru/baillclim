![HACS](https://img.shields.io/badge/HACS-gray?style=for-the-badge)
![CUSTOM](https://img.shields.io/badge/CUSTOM-blue?style=for-the-badge)
![RELEASE](https://img.shields.io/badge/RELEASE-gray?style=for-the-badge)
![VERSION](https://img.shields.io/badge/V3.0.0-blue?style=for-the-badge)

# 🌡️ BaillClim – Intégration BaillConnect pour Home Assistant (v3.0)

**Publié par [@herbru](https://github.com/hebrru)**

---

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

---

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

```
https://github.com/hebrru/baillclim
```

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

## ⚙️ Configuration manuelle obligatoire

### 1️⃣ Remplacer l’ID de régulation (`group_id`)

Dans le fichier `const.py`, remplacez les `XXX` par l’ID affiché dans l’URL quand vous êtes connecté à BaillConnect.

```python
# custom_components/baillclim/const.py

REGULATIONS_URL = "https://www.baillconnect.com/client/regulations/XXX"
COMMAND_URL = "https://www.baillconnect.com/api-client/regulations/XXX"
```

Par exemple, si l’URL dans votre navigateur contient `regulations/270`, utilisez :

```python
REGULATIONS_URL = "https://www.baillconnect.com/client/regulations/270"
COMMAND_URL = "https://www.baillconnect.com/api-client/regulations/270"
```

---

### 2️⃣ Adapter les IDs de thermostats dans `sensor.py`

Par défaut, seuls les thermostats avec des IDs compris entre 500 et 515 sont pris en compte.

Vous devez modifier cette ligne :

```python
if XXXX <= tid <= XXXX:  # 👉 Remplacez les XXXX par vos IDs réels
```

✅ Exemple si vos thermostats ont les IDs `10860` à `10870` :

```python
if 10860 <= tid <= 10870:
```

📍 Pour trouver vos IDs, allez dans l’entité `sensor.debug_baillconnect_data`  
➡️ Puis ouvrez l’onglet **"Attributs"**, vous verrez :

```yaml
thermostats:
  - id: 10866
    name: "Salon"
    temperature: 26.5
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
C’est ma **première intégration Home Assistant**, et aussi la **première fois que je publie sur GitHub**.  
J’ai encore des progrès à faire, mais je suis très motivé !

🧠 Suggestions, bugs ou idées d’amélioration ?  
Vos retours sont les bienvenus ! Ouvrez une issue ici 👉 [Issues GitHub](https://github.com/hebrru/baillclim/issues)

---

## 📄 Licence

MIT – Libre de réutilisation, modification et intégration dans vos projets.

---

## 👤 Auteur

Développé par **herbru**  
🔗 GitHub : [hebrru/baillclim](https://github.com/hebrru/baillclim)

---

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>
