"""Predlošci dokumenata (bivši document_templates.json)."""
from __future__ import annotations

import json

DOCUMENT_TEMPLATES = json.loads(r"""
[
  {
    "id": "pristupnica_krizma",
    "name": "Pristupnica za sv. Potvrdu",
    "category": "krizma",
    "fields": [
      "ime_prezime",
      "datum_rodjenja",
      "datum_krstenja",
      "kum",
      "datum_potvrde",
      "zupnik",
      "zupa"
    ],
    "body": "<div class=\"print-doc\">\n        <h1 style=\"text-align:center;font-family:Georgia,serif\">PRISTUPNICA ZA SAKRAMENT SVETE POTVRDE</h1>\n        <p style=\"margin-top:2em\">Ja, don <strong>{{zupnik}}</strong>, župnik župe <strong>{{zupa}}</strong>, potvrđujem da je:</p>\n        <p><strong>Ime i prezime:</strong> {{ime_prezime}}</p>\n        <p><strong>Datum rođenja:</strong> {{datum_rodjenja}}</p>\n        <p><strong>Datum krštenja:</strong> {{datum_krstenja}}</p>\n        <p><strong>Kum/ka za potvrdu:</strong> {{kum}}</p>\n        <p style=\"margin-top:2em\">Datum potvrde: <strong>{{datum_potvrde}}</strong></p>\n        <p style=\"margin-top:3em\">Potpis župnika: _________________________</p>\n        <p>Mjesto i datum: {{zupa}}, {{danas}}</p>\n      </div>"
  },
  {
    "id": "potvrda_krsenja",
    "name": "Potvrda o krštenju (izvadak)",
    "category": "krsenje",
    "fields": [
      "ime_djeteta",
      "datum_krstenja",
      "roditelji",
      "kumovi",
      "maticni_broj",
      "zupnik",
      "zupa"
    ],
    "body": "<div class=\"print-doc\">\n        <h2 style=\"text-align:center\">IZVADAK IZ MATIČNE KNJIGE KRŠTENIH</h2>\n        <p>Župa: <strong>{{zupa}}</strong></p>\n        <p>Dijete: <strong>{{ime_djeteta}}</strong></p>\n        <p>Kršteno: <strong>{{datum_krstenja}}</strong></p>\n        <p>Roditelji: {{roditelji}}</p>\n        <p>Kum(ovi): {{kumovi}}</p>\n        <p>Matični broj: {{maticni_broj}}</p>\n        <p style=\"margin-top:2em\">Izdano u {{zupa}}, {{danas}}.</p>\n        <p>Župnik: {{zupnik}}</p>\n      </div>"
  },
  {
    "id": "raspored_nakana",
    "name": "Raspored misnih nakana (tjedan)",
    "category": "nakane",
    "fields": [
      "tjedan_od",
      "zupa"
    ],
    "body": "<div class=\"print-doc\">\n        <h2 style=\"text-align:center\">RASPORED MOLITVENIH NAKANA</h2>\n        <p>Župa {{zupa}} · tjedan od {{tjedan_od}}</p>\n        <table border=\"1\" cellpadding=\"8\" style=\"width:100%;border-collapse:collapse;margin-top:1em\">\n          <thead><tr><th>Datum</th><th>Misa</th><th>Namjera</th><th>Stipendij</th></tr></thead>\n          <tbody>{{tablica_nakana}}</tbody>\n        </table>\n      </div>"
  },
  {
    "id": "izvjestaj_dekanska_vizitacija",
    "name": "Izvješće o dekanskoj vizitaciji",
    "category": "ured",
    "fields": [
      "godina",
      "stanje_zupe",
      "preporuke",
      "zupnik",
      "zupa",
      "danas"
    ],
    "body": "<div class=\"print-doc\">\n        <h2 style=\"text-align:center\">IZVJEŠĆE O DEKANSKOJ VIZITACIJI</h2>\n        <p>Župa: <strong>{{zupa}}</strong> · Godina: {{godina}}</p>\n        <p><strong>Stanje župe:</strong></p><p>{{stanje_zupe}}</p>\n        <p><strong>Preporuke dekana:</strong></p><p>{{preporuke}}</p>\n        <p style=\"margin-top:2em\">{{zupa}}, {{danas}}</p>\n        <p>Župnik: {{zupnik}}</p>\n      </div>"
  },
  {
    "id": "zapisnik_kanonska_vizitacija",
    "name": "Zapisnik kanonske vizitacije",
    "category": "ured",
    "fields": [
      "datum",
      "prisutni",
      "dnevni_red",
      "zakljucci",
      "zupnik",
      "zupa"
    ],
    "body": "<div class=\"print-doc\">\n        <h2 style=\"text-align:center\">ZAPISNIK KANONSKE VIZITACIJE</h2>\n        <p>Župa: {{zupa}} · Datum: {{datum}}</p>\n        <p><strong>Prisutni:</strong> {{prisutni}}</p>\n        <p><strong>Tijek vizitacije:</strong></p><p>{{dnevni_red}}</p>\n        <p><strong>Zaključci i nalozi:</strong></p><p>{{zakljucci}}</p>\n        <p style=\"margin-top:2em\">Potpis župnika: {{zupnik}}</p>\n      </div>"
  },
  {
    "id": "potvrda_lukno",
    "name": "Potvrda o uplati župnog lukna",
    "category": "lukno",
    "fields": [
      "obitelj",
      "adresa",
      "godina",
      "iznos",
      "datum_uplate",
      "zupnik",
      "zupa"
    ],
    "body": "<div class=\"print-doc\">\n        <h2 style=\"text-align:center\">POTVRDA O UPLATI ŽUPNOG LUKNA</h2>\n        <p>Župa: <strong>{{zupa}}</strong></p>\n        <p>Obitelj: <strong>{{obitelj}}</strong></p>\n        <p>Adresa: {{adresa}}</p>\n        <p>Godina: <strong>{{godina}}</strong></p>\n        <p>Iznos: <strong>{{iznos}} €</strong></p>\n        <p>Datum uplate: {{datum_uplate}}</p>\n        <p style=\"margin-top:2em\">Potvrđujemo primitak navedenog iznosa za župno lukno.</p>\n        <p style=\"margin-top:2em\">{{zupa}}, {{danas}}</p>\n        <p>Župnik: {{zupnik}}</p>\n      </div>"
  }
]
""")
