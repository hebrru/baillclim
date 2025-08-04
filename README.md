# 🌡️ BaillClim – Intégration BaillConnect pour Home Assistant

[![HACS](https://img.shields.io/badge/HACS-gray?style=for-the-badge)](https://hacs.xyz)
[![CUSTOM](https://img.shields.io/badge/CUSTOM-blue?style=for-the-badge)](https://github.com/hebrru/baillclim)
[![RELEASE](https://img.shields.io/badge/RELEASE-latest?style=for-the-badge)](https://github.com/hebrru/baillclim/releases)

---

## 🔧 Description

**BaillClim** est une intégration personnalisée pour **Home Assistant** permettant de piloter vos thermostats et zones via le portail **BaillConnect** (https://www.baillconnect.com).

### Entités créées automatiquement

| Type      | Entité                                | Description                                                  |
|-----------|----------------------------------------|--------------------------------------------------------------|
| `climate` | `climate.baillclim_XXX`                | Thermostats avec on/off, consignes froid/chaud, température |
| `sensor`  | `sensor.baillclim_temp_XXX`            | Température actuelle de chaque thermostat                   |
| `select`  | `select.mode_climatisation_XXX`        | Mode global (Arrêt, Froid, Chauffage, etc.)                 |
| `switch`  | `switch.zone_XXX_active`               | Activation ON/OFF de chaque zone                            |
| `sensor`  | `sensor.debug_baillconnect_data`       | Données JSON brutes pour debug                              |

---

## 🚀 Installation via HACS

1. Ajoutez le dépôt :  
   `https://github.com/hebrru/baillclim`

2. HACS → Intégrations → (⋮) → Dépôts personnalisés  
   Choisir **Intégration** et coller l’URL.

3. Recherchez "BaillClim", installez et redémarrez Home Assistant.

4. Allez dans **Paramètres → Appareils & Services → Ajouter une intégration**

5. Recherchez **BaillClim** et entrez vos identifiants BaillConnect.

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
      entity_id: select.mode_climatisation_270
      option: Ventilation
```

---

## 🧠 Suggestions / Bugs / Améliorations

👉 Créez une issue sur [GitHub](https://github.com/hebrru/baillclim/issues)

---

## 👤 Auteur

Hervé G. – [@hebrru](https://github.com/hebrru)  
☕ [Buy Me A Coffee](https://www.buymeacoffee.com/herbru01d)