
# 🌡️ BaillClim – Intégration BaillConnect pour Home Assistant (v5.0.0)
![HACS](https://img.shields.io/badge/HACS-gray?style=for-the-badge) ![CUSTOM](https://img.shields.io/badge/CUSTOM-blue?style=for-the-badge) ![RELEASE](https://img.shields.io/badge/RELEASE-green?style=for-the-badge) ![VERSION](https://img.shields.io/badge/V5.0.0-blue?style=for-the-badge)

Développé par [@hebrru](https://github.com/hebrru)

<a href="https://www.buymeacoffee.com/herbru01d" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

---

## 🔧 Description

**BaillClim** est une intégration personnalisée pour **Home Assistant** permettant de piloter vos thermostats connectés via le portail **BaillConnect** (baillconnect.com).

---

## 🆕 Nouveautés de la version 5.0.0

✅ Intégration entièrement réécrite et stabilisée  
✅ Entités climate complètes (on/off, température, mode)  
✅ Affichage dynamique des consignes froides / chaudes  
✅ Sélecteur de mode UC (Arrêt, Froid, Chauffage, Ventilation, Déshumidificateur)  
✅ Capteur de température pour chaque thermostat  
✅ Switch de contrôle ON/OFF pour chaque zone active  
✅ Capteur debug contenant toutes les données brutes  
✅ Aucun identifiant dur : détection dynamique de tous les thermostats et zones

---

## 🚀 Installation via HACS

1. Ajouter le dépôt personnalisé :

```
https://github.com/hebrru/baillclim
```

2. HACS → Intégrations → (⋮) → Dépôts personnalisés  
3. Choisir la catégorie : `Intégration`  
4. Installer l’intégration  
5. Redémarrer Home Assistant  
6. Aller dans : `Paramètres → Appareils & Services → Ajouter une intégration`  
7. Rechercher **BaillClim**, puis entrer :  
   - Email BaillConnect  
   - Mot de passe BaillConnect

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

**Hervé G.**  
GitHub : [hebrru](https://github.com/hebrru)  
☕ [Buy Me A Coffee](https://www.buymeacoffee.com/herbru01d)
