"""Konfiguracija župnog listića (bivši zupni_listic_config.json)."""
from __future__ import annotations

import json

ZUPNI_LISTIC_CONFIG = json.loads(r"""
{
  "blockTypes": {
    "header": {
      "label": "Zaglavlje",
      "desc": "Naziv župe, tjedan, župnik — automatski iz postavki",
      "auto": true,
      "fixed": true
    },
    "mass_schedule": {
      "label": "Raspored misa",
      "desc": "Automatski iz modula Mise",
      "auto": true
    },
    "nakane": {
      "label": "Molitvene nakane",
      "desc": "Automatski iz kalendara nakana za tjedan",
      "auto": true
    },
    "announcements": {
      "label": "Obavijesti župe",
      "desc": "Upišite obavijesti koje želite objaviti u ovom izdanju",
      "auto": false
    },
    "custom_text": {
      "label": "Slobodni tekst",
      "desc": "Naslov i oblikovani tekst",
      "auto": false
    },
    "sacraments": {
      "label": "Sakramenti i događaji",
      "desc": "Krštenja, vjenčanja, pogrebi, događaji",
      "auto": true
    },
    "contact": {
      "label": "Kontakt ureda",
      "desc": "Telefon, e-mail i adresa župe",
      "auto": true
    },
    "footer": {
      "label": "Podnožje",
      "desc": "Kratka oblikovana napomena na dnu listića",
      "auto": false,
      "fixed": true
    }
  },
  "defaultLayout": {
    "blocks": [
      {
        "id": "blk_hdr",
        "type": "header",
        "enabled": true
      },
      {
        "id": "blk_ms",
        "type": "mass_schedule",
        "enabled": true,
        "title": "Raspored sv. misa"
      },
      {
        "id": "blk_nk",
        "type": "nakane",
        "enabled": true,
        "title": "Molitvene nakane"
      },
      {
        "id": "blk_ob",
        "type": "announcements",
        "enabled": true,
        "title": "Obavijesti župe"
      },
      {
        "id": "blk_kt",
        "type": "custom_text",
        "enabled": true,
        "title": "Pobožnosti",
        "body": ""
      },
      {
        "id": "blk_sk",
        "type": "sacraments",
        "enabled": true,
        "title": "Sakramenti i događaji"
      },
      {
        "id": "blk_ku",
        "type": "contact",
        "enabled": true,
        "title": "Župni ured"
      },
      {
        "id": "blk_ft",
        "type": "footer",
        "enabled": true,
        "title": "",
        "body": "Župni listić — izdanje za župljane."
      }
    ],
    "updatedAt": null
  },
  "defaultTemplate": {
    "fileName": "zupni-listic-zadani.html",
    "updatedAt": null,
    "html": ""
  },
  "fieldLabels": {
    "biskupija": "Biskupija / nadbiskupija",
    "zupa": "Naziv župe",
    "grad": "Mjesto",
    "zupnik": "Župnik",
    "tjedan_od": "Tjedan od",
    "tjedan_do": "Tjedan do",
    "liturgijska_boja": "Liturgijska boja",
    "misni_raspored": "Raspored misa",
    "nakane_tjedan": "Nakane (tjedan)",
    "obavijesti_zupe": "Obavijesti župe",
    "kateheza_pobožnosti": "Pobožnosti",
    "sakramenti_dogadaji": "Sakramenti i događaji",
    "kontakt_ured": "Kontakt župnog ureda",
    "napomena_listica": "Napomena na listiću",
    "datum_izdavanja": "Datum izdavanja"
  }
}
""")
