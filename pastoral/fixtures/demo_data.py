"""Demo parish podaci za seed (bivši demo_data.json)."""
from __future__ import annotations

import json

DEMO_PARISH_DATA = json.loads(r"""
{
  "massSchedule": [
    {
      "id": "ms1",
      "day": "Nedjelja",
      "time": "07:30",
      "weekdays": [
        0
      ],
      "location": "Župna crkva",
      "notes": ""
    },
    {
      "id": "ms2",
      "day": "Nedjelja",
      "time": "09:00",
      "weekdays": [
        0
      ],
      "location": "Župna crkva",
      "notes": ""
    },
    {
      "id": "ms3",
      "day": "Nedjelja",
      "time": "11:00",
      "weekdays": [
        0
      ],
      "location": "Župna crkva",
      "notes": "Djeca i obitelji"
    },
    {
      "id": "ms4",
      "day": "Nedjelja",
      "time": "18:00",
      "weekdays": [
        0
      ],
      "location": "Župna crkva",
      "notes": ""
    },
    {
      "id": "ms5",
      "day": "Pon–Pet",
      "time": "07:30",
      "weekdays": [
        1,
        2,
        3,
        4,
        5
      ],
      "location": "Župna crkva",
      "notes": ""
    },
    {
      "id": "ms6",
      "day": "Subota",
      "time": "18:00",
      "weekdays": [
        6
      ],
      "location": "Župna crkva",
      "notes": ""
    }
  ],
  "massExceptions": [],
  "intentions": [
    {
      "id": "n1",
      "date": "2026-06-09",
      "massTime": "18:00",
      "intentionFor": "Pokoj duše Ivana H.",
      "stipend": 50,
      "paid": true,
      "notes": ""
    },
    {
      "id": "n2",
      "date": "2026-06-10",
      "massTime": "07:30",
      "intentionFor": "Zdravlje obitelji",
      "stipend": 30,
      "paid": false,
      "notes": ""
    },
    {
      "id": "n4",
      "date": "2026-06-14",
      "massTime": "11:00",
      "intentionFor": "Za uspjeh na ispitu",
      "stipend": 30,
      "paid": false,
      "notes": ""
    }
  ],
  "baptisms": [
    {
      "id": "b1",
      "childName": "Luka Novak",
      "birthDate": "2024-08-12",
      "baptismDate": "2026-06-23",
      "parents": "Iva i Marko Novak",
      "godparents": "Ana i Josip",
      "celebrant": "vlč. Krunoslav Karas",
      "registryNo": "2026/12",
      "status": "priprema",
      "gift": 0,
      "godparentCertReceived": false
    },
    {
      "id": "b2",
      "childName": "Mia Kovač",
      "birthDate": "2025-11-03",
      "baptismDate": "2026-07-09",
      "parents": "Marija i Petar Kovač",
      "godparents": "—",
      "celebrant": "",
      "registryNo": "",
      "status": "upis",
      "gift": 50,
      "godparentCertReceived": true
    }
  ],
  "firstCommunion": [
    {
      "id": "fc1",
      "year": 2026,
      "groupName": "Skupina A",
      "celebrant": "vlč. Krunoslav Karas",
      "ceremonyDate": "2026-09-07",
      "groupFee": 120,
      "groupFeePaid": false,
      "candidates": [
        {
          "id": "c1",
          "firstName": "Ema",
          "lastName": "Horvat",
          "name": "Ema Horvat",
          "school": "OŠ Ivana Brlić-Mažuranić",
          "class": "4.b",
          "parent1FirstName": "Ana",
          "parent1LastName": "Horvat",
          "parent2FirstName": "Petar",
          "parent2LastName": "Horvat",
          "parents": "Ana Horvat i Petar Horvat",
          "paid": true
        },
        {
          "id": "c2",
          "firstName": "Filip",
          "lastName": "Novak",
          "name": "Filip Novak",
          "school": "OŠ Ivana Brlić-Mažuranić",
          "class": "4.a",
          "parent1FirstName": "Iva",
          "parent1LastName": "Novak",
          "parent2FirstName": "Marko",
          "parent2LastName": "Novak",
          "parents": "Iva Novak i Marko Novak",
          "paid": false
        }
      ]
    }
  ],
  "confirmations": [
    {
      "id": "conf2026",
      "year": 2026,
      "bishop": "Đakovačko-osječki nadbiskup",
      "ceremonyDate": "2026-10-07",
      "groupFee": 45,
      "groupFeePaid": false,
      "candidates": [
        {
          "id": "cr1",
          "name": "Lucija Horvat",
          "birthDate": "2012-03-05",
          "school": "OŠ Sv. Marka",
          "class": "7.a",
          "group": "A",
          "baptized": "2012-06-10",
          "sponsor": "Ana Horvat",
          "status": "priprema",
          "oib": ""
        },
        {
          "id": "cr2",
          "name": "Matej Kovač",
          "birthDate": "2011-09-18",
          "school": "OŠ Sv. Marka",
          "class": "8.b",
          "group": "A",
          "baptized": "2011-12-01",
          "sponsor": "Petar Kovač",
          "status": "priprema",
          "oib": ""
        },
        {
          "id": "cr3",
          "name": "Sara Novak",
          "birthDate": "2012-01-22",
          "school": "OŠ Centar",
          "class": "7.b",
          "group": "B",
          "baptized": "2012-04-15",
          "sponsor": "Iva Novak",
          "status": "pristupnica",
          "oib": ""
        }
      ]
    },
    {
      "id": "conf2025",
      "year": 2025,
      "bishop": "Đakovačko-osječki nadbiskup",
      "ceremonyDate": "2025-05-18",
      "groupFee": 40,
      "groupFeePaid": true,
      "groupFeePaidAt": "2025-04-01",
      "candidates": [
        {
          "id": "cr0",
          "name": "Marko Babić",
          "birthDate": "2011-07-01",
          "school": "OŠ Sv. Marka",
          "class": "8.a",
          "group": "A",
          "baptized": "2011-09-12",
          "sponsor": "Marija B.",
          "status": "potvrđen",
          "oib": ""
        }
      ]
    }
  ],
  "weddings": [
    {
      "id": "w1",
      "groomName": "Josip Novak",
      "brideName": "Marta Horvat",
      "couple": "Marta Horvat & Josip Novak",
      "weddingDate": "2026-07-24",
      "church": "Crkva bl. Djevice Marije",
      "preparatorySessions": 3,
      "documentsOk": true,
      "celebrant": "vlč. Krunoslav Karas",
      "groomSponsor": "Petar Kovač",
      "brideSponsor": "Ana Horvat",
      "witnesses": "Petar Kovač, Ana Horvat",
      "contact": "091 444 5555",
      "status": "dogovoreno",
      "stipend": 200,
      "stipendPaid": false
    }
  ],
  "funerals": [
    {
      "id": "f1",
      "deceased": "+ fra Ante Burić",
      "deathDate": "2026-06-08",
      "funeralDate": "2026-06-12",
      "celebrant": "vlč. Krunoslav Karas",
      "massPlanned": true,
      "massDate": "2026-06-12",
      "massTime": "10:00",
      "cemetery": "Gradsko groblje Slavonski Brod",
      "cemeteryLocation": "Ulica fra Grge Martića 1, Slavonski Brod",
      "familyContact": "Obitelj Burić 091 000 1111",
      "status": "potvrđeno",
      "stipend": 50,
      "stipendPaid": false
    }
  ],
  "anointing": [
    {
      "id": "a1",
      "person": "Stjepan Marić",
      "address": "Dom za starije",
      "location": "Ulica Ante Starčevića 12, Slavonski Brod",
      "scheduled": "2026-06-13",
      "scheduledTime": "15:30",
      "priest": "vlč. Krunoslav Karas",
      "contact": "Kći Marija 091 777 8888",
      "notes": "Soba 214, kućna posjeta",
      "status": "dogovoreno",
      "done": false,
      "stipend": 0,
      "stipendPaid": true
    }
  ],
  "parishDebts": [
    {
      "id": "pd1",
      "direction": "payable",
      "year": 2026,
      "category": "režije",
      "label": "EP SB — režija crkve Q2",
      "amount": 320,
      "paid": false,
      "contact": "Elektroprivreda SB",
      "dueDate": "2026-06-19",
      "notes": ""
    },
    {
      "id": "pd2",
      "direction": "receivable",
      "year": 2025,
      "category": "ostalo",
      "label": "Popravak orgulje — obećana donacija",
      "amount": 500,
      "paid": false,
      "contact": "Nepoznati donator",
      "dueDate": "2025-12-31",
      "notes": "ŽEV"
    }
  ],
  "invoices": [
    {
      "id": "inv1",
      "number": "2026-001",
      "issueDate": "2026-05-30",
      "dueDate": "2026-06-14",
      "payerName": "Obitelj Kovač",
      "payerAddress": "Kovačeva ulica 8",
      "payerOib": "",
      "category": "lukno",
      "description": "Župno lukno 2025",
      "amount": 150,
      "vatRate": 0,
      "total": 150,
      "status": "izdan",
      "paidAmount": 0,
      "paidAt": "",
      "linkedSource": {
        "type": "contribution",
        "familyId": "fam2",
        "year": 2025
      },
      "notes": ""
    },
    {
      "id": "inv2",
      "number": "2026-002",
      "issueDate": "2026-06-06",
      "dueDate": "2026-06-23",
      "payerName": "Petar Kovač",
      "payerAddress": "",
      "category": "nakane",
      "description": "Misna nakana — Zdravlje obitelji",
      "amount": 30,
      "vatRate": 0,
      "total": 30,
      "status": "placen",
      "paidAmount": 30,
      "paidAt": "2026-06-08",
      "linkedSource": {
        "type": "intention",
        "id": "n2"
      },
      "notes": ""
    }
  ],
  "streets": [
    {
      "id": "st1",
      "name": "Ulica Cvijete",
      "zone": "Centar župe",
      "sortOrder": 1,
      "notes": "Blok oko crkve"
    },
    {
      "id": "st2",
      "name": "Markova ulica",
      "zone": "Centar župe",
      "sortOrder": 2,
      "notes": ""
    },
    {
      "id": "st3",
      "name": "Bolnička ulica",
      "zone": "Istočni kvart",
      "sortOrder": 3,
      "notes": "Više starijih vjernika"
    },
    {
      "id": "st4",
      "name": "Kovačeva ulica",
      "zone": "Sjever",
      "sortOrder": 4,
      "notes": ""
    },
    {
      "id": "st5",
      "name": "Novakov prolaz",
      "zone": "Sjever",
      "sortOrder": 5,
      "notes": ""
    }
  ],
  "families": [
    {
      "id": "fam1",
      "surname": "Horvat",
      "streetId": "st1",
      "address": "Ulica Cvijete 12",
      "phone": "091 111 1111",
      "email": "horvat@demo.hr",
      "status": "aktivna",
      "preferredMass": "09:00",
      "pastoralNotes": "Redoviti prispjeci. Ana — ŽPV. Djeca u krizmi 2026.",
      "originPlace": "Slavonski Brod",
      "lastVisit": "2026-05-10",
      "tags": [
        "ŽPV",
        "krizma 2026"
      ],
      "husband": {
        "name": "Petar Horvat",
        "birthYear": "1983",
        "birthPlace": "Slavonski Brod",
        "baptismDate": "1983-06-12",
        "baptismPlace": "SB",
        "weddingChurch": "1998",
        "weddingCivil": "1998",
        "notes": ""
      },
      "wife": {
        "name": "Ana Horvat",
        "birthYear": "1985",
        "birthPlace": "Slavonski Brod",
        "baptismDate": "1985-04-20",
        "baptismPlace": "SB",
        "weddingChurch": "1998",
        "weddingCivil": "1998",
        "notes": "ŽPV"
      },
      "relatives": [
        {
          "id": "rel1",
          "name": "Stjepan Horvat",
          "relation": "rođak",
          "birthYear": "1950",
          "notes": "Povremeni posjet"
        }
      ],
      "contributions": [
        {
          "id": "yc1_24",
          "year": 2024,
          "luknoPaid": true,
          "luknoAmount": 140,
          "luknoPaidAt": "2024-02-10",
          "churchDonation": 400,
          "donationDate": "2024-12-20",
          "notes": ""
        },
        {
          "id": "yc1_25",
          "year": 2025,
          "luknoPaid": true,
          "luknoAmount": 150,
          "luknoPaidAt": "2025-01-08",
          "churchDonation": 350,
          "donationDate": "2025-11-05",
          "notes": ""
        },
        {
          "id": "yc1_26",
          "year": 2026,
          "luknoPaid": true,
          "luknoAmount": 150,
          "luknoPaidAt": "2026-01-12",
          "churchDonation": 200,
          "donationDate": "2026-03-01",
          "notes": ""
        }
      ],
      "members": [
        {
          "id": "m1",
          "name": "Ana",
          "birthYear": 1985,
          "relation": "majka",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma",
            "vjenčanje"
          ],
          "roles": [
            "ŽPV"
          ],
          "notes": ""
        },
        {
          "id": "m2",
          "name": "Petar",
          "birthYear": 1983,
          "relation": "otac",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma",
            "vjenčanje"
          ],
          "roles": [],
          "notes": ""
        },
        {
          "id": "m3",
          "name": "Lucija",
          "birthYear": 2012,
          "relation": "kći",
          "sacraments": [
            "krštenje",
            "pričest"
          ],
          "roles": [
            "krizmanik"
          ],
          "notes": "Krizma 2026"
        },
        {
          "id": "m4",
          "name": "Ema",
          "birthYear": 2016,
          "relation": "kći",
          "sacraments": [
            "krštenje"
          ],
          "roles": [
            "prvopričesnik"
          ],
          "notes": ""
        }
      ]
    },
    {
      "id": "fam2",
      "surname": "Kovač",
      "streetId": "st4",
      "address": "Kovačeva ulica 8",
      "phone": "092 222 3333",
      "email": "kovac@demo.hr",
      "status": "aktivna",
      "preferredMass": "11:00",
      "pastoralNotes": "Posjetiti prije Uskrsa.",
      "lastVisit": "2026-04-10",
      "tags": [],
      "contributions": [
        {
          "id": "yc2_24",
          "year": 2024,
          "luknoPaid": true,
          "luknoAmount": 140,
          "luknoPaidAt": "2024-03-01",
          "churchDonation": 250,
          "donationDate": "",
          "notes": ""
        },
        {
          "id": "yc2_25",
          "year": 2025,
          "luknoPaid": false,
          "luknoAmount": 150,
          "luknoPaidAt": "",
          "churchDonation": 0,
          "donationDate": "",
          "notes": "Podsjetnik poslan"
        },
        {
          "id": "yc2_26",
          "year": 2026,
          "luknoPaid": false,
          "luknoAmount": 150,
          "luknoPaidAt": "",
          "churchDonation": 100,
          "donationDate": "2026-02-15",
          "notes": ""
        }
      ],
      "members": [
        {
          "id": "m5",
          "name": "Marija",
          "birthYear": 1980,
          "relation": "majka",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma"
          ],
          "roles": [],
          "notes": ""
        },
        {
          "id": "m6",
          "name": "Ivan",
          "birthYear": 1978,
          "relation": "otac",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma"
          ],
          "roles": [],
          "notes": ""
        },
        {
          "id": "m7",
          "name": "Matej",
          "birthYear": 2011,
          "relation": "sin",
          "sacraments": [
            "krštenje",
            "pričest"
          ],
          "roles": [
            "krizmanik"
          ],
          "notes": ""
        },
        {
          "id": "m8",
          "name": "Mia",
          "birthYear": 2025,
          "relation": "kći",
          "sacraments": [],
          "roles": [],
          "notes": "Priprema krštenja"
        }
      ]
    },
    {
      "id": "fam3",
      "surname": "Novak",
      "streetId": "st5",
      "address": "Novakov prolaz 3",
      "phone": "098 333 4444",
      "email": "",
      "status": "aktivna",
      "preferredMass": "18:00",
      "pastoralNotes": "",
      "lastVisit": "",
      "tags": [],
      "contributions": [
        {
          "id": "yc3_25",
          "year": 2025,
          "luknoPaid": true,
          "luknoAmount": 150,
          "luknoPaidAt": "2025-02-20",
          "churchDonation": 150,
          "donationDate": "",
          "notes": ""
        },
        {
          "id": "yc3_26",
          "year": 2026,
          "luknoPaid": false,
          "luknoAmount": 150,
          "luknoPaidAt": "",
          "churchDonation": 0,
          "donationDate": "",
          "notes": ""
        }
      ],
      "members": [
        {
          "id": "m9",
          "name": "Iva",
          "birthYear": 1990,
          "relation": "majka",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma"
          ],
          "roles": [],
          "notes": ""
        },
        {
          "id": "m10",
          "name": "Marko",
          "birthYear": 1988,
          "relation": "otac",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma"
          ],
          "roles": [],
          "notes": ""
        },
        {
          "id": "m11",
          "name": "Luka",
          "birthYear": 2024,
          "relation": "sin",
          "sacraments": [],
          "roles": [],
          "notes": "Krštenje zakazano"
        },
        {
          "id": "m12",
          "name": "Filip",
          "birthYear": 2016,
          "relation": "sin",
          "sacraments": [
            "krštenje",
            "pričest"
          ],
          "roles": [
            "prvopričesnik"
          ],
          "notes": ""
        }
      ]
    },
    {
      "id": "fam4",
      "surname": "Babić",
      "streetId": "st3",
      "address": "Bolnička ulica 12",
      "phone": "091 555 6666",
      "email": "babic@demo.hr",
      "status": "aktivna",
      "preferredMass": "07:30",
      "pastoralNotes": "Marija — kućna sv. Pričest. Stjepan u domu.",
      "lastVisit": "2026-06-02",
      "tags": [
        "sv. Pričest",
        "bolesnik"
      ],
      "contributions": [
        {
          "id": "yc4_24",
          "year": 2024,
          "luknoPaid": true,
          "luknoAmount": 120,
          "luknoPaidAt": "2024-01-05",
          "churchDonation": 600,
          "donationDate": "2024-06-01",
          "notes": "Redovita donatorica"
        },
        {
          "id": "yc4_25",
          "year": 2025,
          "luknoPaid": true,
          "luknoAmount": 150,
          "luknoPaidAt": "2025-01-10",
          "churchDonation": 500,
          "donationDate": "",
          "notes": ""
        },
        {
          "id": "yc4_26",
          "year": 2026,
          "luknoPaid": true,
          "luknoAmount": 150,
          "luknoPaidAt": "2026-01-05",
          "churchDonation": 300,
          "donationDate": "2026-01-20",
          "notes": ""
        }
      ],
      "members": [
        {
          "id": "m13",
          "name": "Marija",
          "birthYear": 1955,
          "relation": "majka",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma"
          ],
          "roles": [],
          "notes": "Nepokretna"
        },
        {
          "id": "m14",
          "name": "Marko",
          "birthYear": 2011,
          "relation": "unuk",
          "sacraments": [
            "krštenje",
            "pričest",
            "krizma"
          ],
          "roles": [],
          "notes": ""
        }
      ]
    }
  ],
  "parishioners": [
    {
      "id": "p1",
      "family": "Horvat",
      "name": "Ana",
      "phone": "091 111 1111",
      "email": "ana@demo.hr",
      "status": "aktivan",
      "roles": [
        "ŽPV"
      ]
    },
    {
      "id": "p2",
      "family": "Horvat",
      "name": "Petar",
      "phone": "091 111 1112",
      "status": "aktivan",
      "roles": []
    },
    {
      "id": "p3",
      "family": "Kovač",
      "name": "Marija",
      "phone": "092 222 3333",
      "status": "aktivan",
      "roles": []
    }
  ],
  "luknoDefaultAmount": 150,
  "tasks": [
    {
      "id": "t1",
      "title": "Izvješće za biskupiju — kvartal",
      "due": "2026-06-23",
      "priority": "visoka",
      "done": false,
      "category": "biskupija"
    },
    {
      "id": "t2",
      "title": "Sastanak župnog pastoralnog vijeća",
      "due": "2026-06-16",
      "priority": "srednja",
      "done": false,
      "category": "ŽPV"
    },
    {
      "id": "t3",
      "title": "Pregled blagajne (župno ekonomsko vijeće)",
      "due": "2026-06-14",
      "priority": "srednja",
      "done": false,
      "category": "ŽEV"
    }
  ],
  "events": [
    {
      "id": "e1",
      "title": "Župna korizmena obnova",
      "date": "2026-06-19",
      "place": "Župna dvorana",
      "type": "pastoral"
    },
    {
      "id": "e2",
      "title": "Sastanak ministranata",
      "date": "2026-06-13",
      "place": "Sakristija",
      "type": "liturgija"
    }
  ],
  "announcements": [
    {
      "id": "an1",
      "title": "Upis krizmanika 2026",
      "body": "Župa bl. Djevice Marije, Slavonski Brod — prijava u župnom uredu ili putem obrasca do 15. ožujka.",
      "at": "2026-06-09T10:27:30.049Z"
    }
  ],
  "zupniListicIssues": [],
  "publicSubmissions": [],
  "visits": [
    {
      "id": "vis1",
      "scheduled": "2026-06-11",
      "type": "kucna-pricest",
      "person": "Marija Babić",
      "familyId": "fam4",
      "address": "Bolnička ulica 12",
      "priest": "vlč. Krunoslav Karas",
      "purpose": "Kućna sv. Pričest",
      "done": false,
      "report": ""
    },
    {
      "id": "vis2",
      "scheduled": "2026-05-26",
      "type": "obitelj",
      "person": "Obitelj Kovač",
      "familyId": "fam2",
      "address": "Kovačeva ulica 8",
      "priest": "vlč. Krunoslav Karas",
      "purpose": "Pastoralni posjet — lukno",
      "done": true,
      "report": "Razgovor o luknu 2025."
    }
  ],
  "cashbook": [
    {
      "id": "cb1",
      "date": "2026-05-20",
      "type": "ulaz",
      "category": "lukno",
      "ledger": "crkveni",
      "description": "Lukno Horvat 2026",
      "amount": 150,
      "paymentMethod": "gotovina",
      "reportCode": "A-1"
    },
    {
      "id": "cb2",
      "date": "2026-05-25",
      "type": "ulaz",
      "category": "nakane",
      "ledger": "misne",
      "description": "Stipendiji — siječanj",
      "amount": 180,
      "paymentMethod": "žiro",
      "reportCode": "A-1"
    },
    {
      "id": "cb3",
      "date": "2026-06-04",
      "type": "izlaz",
      "category": "materijal",
      "ledger": "crkveni",
      "description": "Materijal za pastoralnu pripremu",
      "amount": 85,
      "paymentMethod": "gotovina",
      "reportCode": "C-1"
    },
    {
      "id": "cb4",
      "date": "2026-05-28",
      "type": "izlaz",
      "category": "kolekta",
      "ledger": "kolekte",
      "description": "Nadbiskupiji BIH",
      "amount": 125,
      "paymentMethod": "žiro",
      "reportCode": "D-1"
    }
  ],
  "registryBooks": [
    {
      "id": "rk1",
      "type": "krštenja",
      "title": "Knjiga rođenih i krštenih",
      "location": "Župni arhiv — sef",
      "lastEntry": "2026-05-26",
      "lastNo": "2026/12",
      "custodian": "vlč. Krunoslav Karas",
      "status": "u župi",
      "notes": "Kan. 535 §2 · izvadci samo iz knjige"
    },
    {
      "id": "rk2",
      "type": "vjenčanja",
      "title": "Knjiga vjenčanih",
      "location": "Župni arhiv — sef",
      "lastEntry": "2024-09-12",
      "lastNo": "2024/08",
      "custodian": "župni ured",
      "status": "u župi",
      "notes": ""
    },
    {
      "id": "rk3",
      "type": "umrli",
      "title": "Knjiga umrlih",
      "location": "Župni arhiv",
      "lastEntry": "2026-06-08",
      "lastNo": "2026/03",
      "custodian": "župni ured",
      "status": "u župi",
      "notes": ""
    },
    {
      "id": "rk4",
      "type": "krizma",
      "title": "Knjiga krizmanika",
      "location": "Župni arhiv",
      "lastEntry": "2025-05-18",
      "lastNo": "2025/41",
      "custodian": "župni ured",
      "status": "u župi",
      "notes": "Digitalna evidencija usklađena s knjigom 2025"
    }
  ],
  "pastoralCouncil": {
    "established": "2008-09-01",
    "lastMeeting": "2026-05-10",
    "nextMeeting": "2026-06-16",
    "members": [
      {
        "id": "zpv1",
        "name": "vlč. Krunoslav Karas",
        "role": "župnik / predsjednik",
        "phone": "091 200 0100",
        "confirmed": true
      },
      {
        "id": "zpv2",
        "name": "Ana Horvat",
        "role": "laik — predstavnik",
        "confirmed": true
      },
      {
        "id": "zpv3",
        "name": "Marija Kovač",
        "role": "laik",
        "confirmed": true
      },
      {
        "id": "zpv4",
        "name": "Ivan Perić",
        "role": "laik",
        "confirmed": true
      },
      {
        "id": "zpv5",
        "name": "Petar Novak",
        "role": "laik",
        "confirmed": true
      },
      {
        "id": "zpv6",
        "name": "Josip Marić",
        "role": "laik — ŽEV",
        "confirmed": true
      },
      {
        "id": "zpv7",
        "name": "Marta Burić",
        "role": "laik",
        "confirmed": false
      }
    ]
  },
  "economicCouncil": {
    "budgetYear": 2026,
    "lastReview": "2026-04-10",
    "nextReview": "2026-06-14",
    "members": [
      {
        "id": "zev1",
        "name": "Josip Marić",
        "role": "predsjednik",
        "confirmed": true
      },
      {
        "id": "zev2",
        "name": "Ana Horvat",
        "role": "član",
        "confirmed": true
      },
      {
        "id": "zev3",
        "name": "Marko Babić",
        "role": "član",
        "confirmed": true
      }
    ]
  },
  "parishDecree": {
    "name": "Župa Blažene Djevice Marije",
    "established": "—",
    "territory": "Slavonski Brod (centar)",
    "decreeRef": "Prema kan. 515–519 · II. sinoda đ.-srij. 2008"
  },
  "appGroups": [],
  "appUsers": [],
  "parishPriests": []
}
""")
