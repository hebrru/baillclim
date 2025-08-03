# 🌡️ BaillClim – Intégration BaillConnect pour Home Assistant (v4.2)

![HACS](https://img.shields.io/badge/HACS-gray?style=for-the-badge)
![CUSTOM](https://img.shields.io/badge/CUSTOM-blue?style=for-the-badge)
![RELEASE](https://img.shields.io/badge/RELEASE-yellow?style=for-the-badge)
![VERSION](https://img.shields.io/badge/V4.2-blue?style=for-the-badge)

Développé par [@herbru](https://github.com/hebrru)

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;">
</a>

---

## 🔧 Description

**BaillClim** est une intégration personnalisée pour **Home Assistant** permettant de piloter vos thermostats connectés via le portail **BaillConnect**.

---

## 🆕 Nouveautés de la version 4.2

✅ Mode `heat_cool` complet avec consigne minimale (froide) à gauche et maximale (chaude) à droite  
✅ Lecture et contrôle du mode UC actuel (Arrêt, Froid, Chauffage, Ventilation, Déshumidificateur)  
✅ Refonte du composant `climate` avec support `TARGET_TEMPERATURE_RANGE`  
✅ Détection automatique des thermostats via l'API  
✅ Entités `climate` complètes, on/off + température cible  
✅ Ajout de **2 entités `switch`** pour contrôler ON/OFF des deux zones principales  
✅ Capteur de débogage `sensor.debug_baillconnect_data`  

---

## 🚀 Installation via HACS

1. **Ajouter le dépôt personnalisé** :
   ```
   https://github.com/hebrru/baillclim
   ```
   HACS → Intégrations → (3 points) → Dépôts personnalisés  
   Catégorie : Intégration

2. **Installer l’intégration** via HACS

3. **Redémarrer Home Assistant**

4. Aller dans **Paramètres** → **Appareils & Services** → **Ajouter une intégration**

5. Rechercher **BaillClim** et entrer :
   - Email BaillConnect
   - Mot de passe BaillConnect

---

## ⚙️ Configuration

Par défaut, `group_id` est configuré sur `270`.

Si votre URL est :
```
https://www.baillconnect.com/client/regulations/295
```
Alors remplacez dans `const.py` :
```python
REGULATIONS_URL = "https://www.baillconnect.com/client/regulations/270"
COMMAND_URL = "https://www.baillconnect.com/api-client/regulations/270"
```
Par :
```python
REGULATIONS_URL = "https://www.baillconnect.com/client/regulations/295"
COMMAND_URL = "https://www.baillconnect.com/api-client/regulations/295"
```
Redémarrez ensuite Home Assistant.

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

## 🧠 Suggestions / Bugs / Améliorations

👉 [Créer une issue GitHub](https://github.com/hebrru/baillclim/issues)

---

## 👤 Auteur

**Hervé G. (herbru)**  
GitHub : [hebrru](https://github.com/hebrru)

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;">
</a>

---

## 📄 Licence

**MIT** – Libre de réutilisation, modification et intégration dans vos projets personnels ou professionnels.
