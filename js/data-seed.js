/**
 * Podaci župe — jedna baza (localStorage)
 */
(function (global) {
  const KEY = "pastoral_data";

  function addDays(n) {
    const d = new Date();
    d.setDate(d.getDate() + n);
    return d.toISOString().slice(0, 10);
  }

  function defaultData() {
    const today = new Date().toISOString().slice(0, 10);
    return {
      massSchedule: [
        { id: "ms1", day: "Nedjelja", time: "07:30" },
        { id: "ms2", day: "Nedjelja", time: "09:00" },
        { id: "ms3", day: "Nedjelja", time: "11:00" },
        { id: "ms4", day: "Nedjelja", time: "18:00" },
        { id: "ms5", day: "Pon–Pet", time: "07:30" },
        { id: "ms6", day: "Subota", time: "18:00" },
      ],
      intentions: [
        { id: "n1", date: today, massTime: "18:00", requestedBy: "Ana Horvat", intentionFor: "Pokoj duše Ivana H.", stipend: 50, paid: true, notes: "" },
        { id: "n2", date: addDays(1), massTime: "07:30", requestedBy: "Petar Kovač", intentionFor: "Zdravlje obitelji", stipend: 30, paid: false, notes: "" },
        { id: "n3", date: addDays(2), massTime: "18:00", requestedBy: "Župni ured", intentionFor: "Zahvala", stipend: 30, paid: true, notes: "Gregorian serija — 3. misa" },
        { id: "n4", date: addDays(5), massTime: "11:00", requestedBy: "Marija B.", intentionFor: "Za uspjeh na ispitu", stipend: 30, paid: false, notes: "" },
      ],
      baptisms: [
        { id: "b1", childName: "Luka Novak", birthDate: "2024-08-12", baptismDate: addDays(14), parents: "Iva i Marko Novak", godparents: "Ana i Josip", celebrant: "vlč. Krunoslav Karas", registryNo: "2026/12", status: "priprema", stipend: 80, stipendPaid: false },
        { id: "b2", childName: "Mia Kovač", birthDate: "2025-11-03", baptismDate: addDays(30), parents: "Marija i Petar Kovač", godparents: "—", celebrant: "", registryNo: "", status: "upis", stipend: 80, stipendPaid: true, stipendPaidAt: "2026-02-01" },
      ],
      firstCommunion: [
        { id: "fc1", year: 2026, groupName: "Skupina A", celebrant: "vlč. Krunoslav Karas", ceremonyDate: addDays(90), groupFee: 120, groupFeePaid: false, candidates: [
          { id: "c1", name: "Ema Horvat", school: "OŠ Ivana Brlić-Mažuranić", class: "4.b", parents: "Ana i Petar" },
          { id: "c2", name: "Filip Novak", school: "OŠ Ivana Brlić-Mažuranić", class: "4.a", parents: "Iva i Marko" },
        ], catechists: [{ id: "k1", name: "Marija Babić", phone: "091 222 3333" }] },
      ],
      confirmations: [
        {
          id: "conf2026",
          year: 2026,
          bishop: "Đakovačko-osječki nadbiskup",
          ceremonyDate: addDays(120),
          groupFee: 45,
          groupFeePaid: false,
          catechists: [
            { id: "ct1", name: "don Josip Novak", role: "župnik", phone: "098 111 2222" },
            { id: "ct2", name: "Ana Marić", role: "kateheta", phone: "091 333 4444" },
            { id: "ct3", name: "Ivan Perić", role: "kateheta", phone: "092 555 6666" },
          ],
          candidates: [
            { id: "cr1", name: "Lucija Horvat", birthDate: "2012-03-05", school: "OŠ Sv. Marka", class: "7.a", group: "A", baptized: "2012-06-10", sponsor: "Ana Horvat", status: "priprema", oib: "" },
            { id: "cr2", name: "Matej Kovač", birthDate: "2011-09-18", school: "OŠ Sv. Marka", class: "8.b", group: "A", baptized: "2011-12-01", sponsor: "Petar Kovač", status: "priprema", oib: "" },
            { id: "cr3", name: "Sara Novak", birthDate: "2012-01-22", school: "OŠ Centar", class: "7.b", group: "B", baptized: "2012-04-15", sponsor: "Iva Novak", status: "pristupnica", oib: "" },
          ],
        },
        {
          id: "conf2025",
          year: 2025,
          bishop: "Đakovačko-osječki nadbiskup",
          ceremonyDate: "2025-05-18",
          groupFee: 40,
          groupFeePaid: true,
          groupFeePaidAt: "2025-04-01",
          catechists: [{ id: "ct0", name: "Ana Marić", role: "kateheta", phone: "091 333 4444" }],
          candidates: [
            { id: "cr0", name: "Marko Babić", birthDate: "2011-07-01", school: "OŠ Sv. Marka", class: "8.a", group: "A", baptized: "2011-09-12", sponsor: "Marija B.", status: "potvrđen", oib: "" },
          ],
        },
      ],
      weddings: [
        { id: "w1", couple: "Marta Horvat & Josip Novak", weddingDate: addDays(45), church: "Crkva bl. Djevice Marije", preparatorySessions: 3, documentsOk: true, celebrant: "vlč. Krunoslav Karas", witnesses: "Ana H., Petar K.", status: "dogovoreno", stipend: 200, stipendPaid: false },
      ],
      funerals: [
        { id: "f1", deceased: "+ fra Ante Burić", deathDate: addDays(-1), funeralDate: addDays(3), cemetery: "Gradsko groblje Slavonski Brod", celebrant: "vlč. Krunoslav Karas", familyContact: "Obitelj Burić 091 000 1111", status: "potvrđeno", stipend: 50, stipendPaid: false },
      ],
      anointing: [
        { id: "a1", person: "Stjepan M.", address: "Dom za starije", scheduled: addDays(4), priest: "vlč. Krunoslav Karas", notes: "Kućna posjeta", done: false, stipend: 0, stipendPaid: true },
      ],
      parishDebts: [
        { id: "pd1", year: 2025, category: "ostalo", label: "Popravak orgulje — obećana donacija", amount: 500, paid: false, contact: "Nepoznati donator", dueDate: "2025-12-31", notes: "ŽEV" },
      ],
      invoices: [
        {
          id: "inv1",
          number: "2026-001",
          issueDate: addDays(-10),
          dueDate: addDays(5),
          payerName: "Obitelj Kovač",
          payerAddress: "Kovačeva ulica 8",
          payerOib: "",
          category: "lukno",
          description: "Župno lukno 2025",
          amount: 150,
          vatRate: 0,
          total: 150,
          status: "izdan",
          paidAmount: 0,
          paidAt: "",
          linkedSource: { type: "contribution", familyId: "fam2", year: 2025 },
          notes: "",
        },
        {
          id: "inv2",
          number: "2026-002",
          issueDate: addDays(-3),
          dueDate: addDays(14),
          payerName: "Petar Kovač",
          payerAddress: "",
          category: "nakane",
          description: "Misna nakana — Zdravlje obitelji",
          amount: 30,
          vatRate: 0,
          total: 30,
          status: "placen",
          paidAmount: 30,
          paidAt: addDays(-1),
          linkedSource: { type: "intention", id: "n2" },
          notes: "",
        },
      ],
      streets: [
        { id: "st1", name: "Ulica Cvijete", zone: "Centar župe", sortOrder: 1, notes: "Blok oko crkve" },
        { id: "st2", name: "Markova ulica", zone: "Centar župe", sortOrder: 2, notes: "" },
        { id: "st3", name: "Bolnička ulica", zone: "Istočni kvart", sortOrder: 3, notes: "Više starijih vjernika" },
        { id: "st4", name: "Kovačeva ulica", zone: "Sjever", sortOrder: 4, notes: "" },
        { id: "st5", name: "Novakov prolaz", zone: "Sjever", sortOrder: 5, notes: "" },
      ],
      families: [
        {
          id: "fam1",
          surname: "Horvat",
          streetId: "st1",
          address: "Ulica Cvijete 12",
          phone: "091 111 1111",
          email: "horvat@demo.hr",
          status: "aktivna",
          preferredMass: "09:00",
          pastoralNotes: "Redoviti prispjeci. Ana — ŽPV. Djeca u krizmi 2026.",
          originPlace: "Slavonski Brod",
          lastVisit: addDays(-30),
          tags: ["ŽPV", "krizma 2026"],
          husband: { name: "Petar Horvat", birthYear: "1983", birthPlace: "Slavonski Brod", baptismDate: "1983-06-12", baptismPlace: "SB", weddingChurch: "1998", weddingCivil: "1998", notes: "" },
          wife: { name: "Ana Horvat", birthYear: "1985", birthPlace: "Slavonski Brod", baptismDate: "1985-04-20", baptismPlace: "SB", weddingChurch: "1998", weddingCivil: "1998", notes: "ŽPV" },
          relatives: [{ id: "rel1", name: "Stjepan Horvat", relation: "rođak", birthYear: "1950", notes: "Povremeni posjet" }],
          contributions: [
            { id: "yc1_24", year: 2024, luknoPaid: true, luknoAmount: 140, luknoPaidAt: "2024-02-10", churchDonation: 400, donationDate: "2024-12-20", notes: "" },
            { id: "yc1_25", year: 2025, luknoPaid: true, luknoAmount: 150, luknoPaidAt: "2025-01-08", churchDonation: 350, donationDate: "2025-11-05", notes: "" },
            { id: "yc1_26", year: 2026, luknoPaid: true, luknoAmount: 150, luknoPaidAt: "2026-01-12", churchDonation: 200, donationDate: "2026-03-01", notes: "" },
          ],
          members: [
            { id: "m1", name: "Ana", birthYear: 1985, relation: "majka", sacraments: ["krštenje", "pričest", "krizma", "vjenčanje"], roles: ["ŽPV"], notes: "" },
            { id: "m2", name: "Petar", birthYear: 1983, relation: "otac", sacraments: ["krštenje", "pričest", "krizma", "vjenčanje"], roles: [], notes: "" },
            { id: "m3", name: "Lucija", birthYear: 2012, relation: "kći", sacraments: ["krštenje", "pričest"], roles: ["krizmanik"], notes: "Krizma 2026" },
            { id: "m4", name: "Ema", birthYear: 2016, relation: "kći", sacraments: ["krštenje"], roles: ["prvopričesnik"], notes: "" },
          ],
        },
        {
          id: "fam2",
          surname: "Kovač",
          streetId: "st4",
          address: "Kovačeva ulica 8",
          phone: "092 222 3333",
          email: "kovac@demo.hr",
          status: "aktivna",
          preferredMass: "11:00",
          pastoralNotes: "Marija — kateheta. Posjetiti prije Uskrsa.",
          lastVisit: addDays(-60),
          tags: ["kateheta"],
          contributions: [
            { id: "yc2_24", year: 2024, luknoPaid: true, luknoAmount: 140, luknoPaidAt: "2024-03-01", churchDonation: 250, donationDate: "", notes: "" },
            { id: "yc2_25", year: 2025, luknoPaid: false, luknoAmount: 150, luknoPaidAt: "", churchDonation: 0, donationDate: "", notes: "Podsjetnik poslan" },
            { id: "yc2_26", year: 2026, luknoPaid: false, luknoAmount: 150, luknoPaidAt: "", churchDonation: 100, donationDate: "2026-02-15", notes: "" },
          ],
          members: [
            { id: "m5", name: "Marija", birthYear: 1980, relation: "majka", sacraments: ["krštenje", "pričest", "krizma"], roles: ["kateheta"], notes: "" },
            { id: "m6", name: "Ivan", birthYear: 1978, relation: "otac", sacraments: ["krštenje", "pričest", "krizma"], roles: [], notes: "" },
            { id: "m7", name: "Matej", birthYear: 2011, relation: "sin", sacraments: ["krštenje", "pričest"], roles: ["krizmanik"], notes: "" },
            { id: "m8", name: "Mia", birthYear: 2025, relation: "kći", sacraments: [], roles: [], notes: "Priprema krštenja" },
          ],
        },
        {
          id: "fam3",
          surname: "Novak",
          streetId: "st5",
          address: "Novakov prolaz 3",
          phone: "098 333 4444",
          email: "",
          status: "aktivna",
          preferredMass: "18:00",
          pastoralNotes: "",
          lastVisit: "",
          tags: [],
          contributions: [
            { id: "yc3_25", year: 2025, luknoPaid: true, luknoAmount: 150, luknoPaidAt: "2025-02-20", churchDonation: 150, donationDate: "", notes: "" },
            { id: "yc3_26", year: 2026, luknoPaid: false, luknoAmount: 150, luknoPaidAt: "", churchDonation: 0, donationDate: "", notes: "" },
          ],
          members: [
            { id: "m9", name: "Iva", birthYear: 1990, relation: "majka", sacraments: ["krštenje", "pričest", "krizma"], roles: [], notes: "" },
            { id: "m10", name: "Marko", birthYear: 1988, relation: "otac", sacraments: ["krštenje", "pričest", "krizma"], roles: [], notes: "" },
            { id: "m11", name: "Luka", birthYear: 2024, relation: "sin", sacraments: [], roles: [], notes: "Krštenje zakazano" },
            { id: "m12", name: "Filip", birthYear: 2016, relation: "sin", sacraments: ["krštenje", "pričest"], roles: ["prvopričesnik"], notes: "" },
          ],
        },
        {
          id: "fam4",
          surname: "Babić",
          streetId: "st3",
          address: "Bolnička ulica 12",
          phone: "091 555 6666",
          email: "babic@demo.hr",
          status: "aktivna",
          preferredMass: "07:30",
          pastoralNotes: "Marija — kućna sv. Pričest. Stjepan u domu.",
          lastVisit: addDays(-7),
          tags: ["sv. Pričest", "bolesnik"],
          contributions: [
            { id: "yc4_24", year: 2024, luknoPaid: true, luknoAmount: 120, luknoPaidAt: "2024-01-05", churchDonation: 600, donationDate: "2024-06-01", notes: "Redovita donatorica" },
            { id: "yc4_25", year: 2025, luknoPaid: true, luknoAmount: 150, luknoPaidAt: "2025-01-10", churchDonation: 500, donationDate: "", notes: "" },
            { id: "yc4_26", year: 2026, luknoPaid: true, luknoAmount: 150, luknoPaidAt: "2026-01-05", churchDonation: 300, donationDate: "2026-01-20", notes: "" },
          ],
          members: [
            { id: "m13", name: "Marija", birthYear: 1955, relation: "majka", sacraments: ["krštenje", "pričest", "krizma"], roles: [], notes: "Nepokretna" },
            { id: "m14", name: "Marko", birthYear: 2011, relation: "unuk", sacraments: ["krštenje", "pričest", "krizma"], roles: [], notes: "" },
          ],
        },
      ],
      parishioners: [
        { id: "p1", family: "Horvat", name: "Ana", phone: "091 111 1111", email: "ana@demo.hr", status: "aktivan", roles: ["ŽPV"] },
        { id: "p2", family: "Horvat", name: "Petar", phone: "091 111 1112", status: "aktivan", roles: [] },
        { id: "p3", family: "Kovač", name: "Marija", phone: "092 222 3333", status: "aktivan", roles: ["kateheta"] },
      ],
      luknoDefaultAmount: 150,
      tasks: [
        { id: "t1", title: "Izvješće za biskupiju — kvartal", due: addDays(14), priority: "visoka", done: false, category: "biskupija" },
        { id: "t2", title: "Sastanak župnog pastoralnog vijeća", due: addDays(7), priority: "srednja", done: false, category: "ŽPV" },
        { id: "t3", title: "Pregled blagajne (župno ekonomsko vijeće)", due: addDays(5), priority: "srednja", done: false, category: "ŽEV" },
      ],
      events: [
        { id: "e1", title: "Župna korizmena obnova", date: addDays(10), place: "Župna dvorana", type: "pastoral" },
        { id: "e2", title: "Sastanak ministranata", date: addDays(4), place: "Sakristija", type: "liturgija" },
      ],
      announcements: [
        { id: "an1", title: "Upis krizmanika 2026", body: "Župa bl. Djevice Marije, Slavonski Brod — prijava u župnom uredu ili putem obrasca do 15. ožujka.", at: new Date().toISOString() },
      ],
      zupniListicTemplate: null,
      zupniListicIssues: [],
      publicSubmissions: [],
      visits: [
        {
          id: "vis1",
          scheduled: addDays(2),
          type: "kucna-pricest",
          person: "Marija Babić",
          familyId: "fam4",
          address: "Bolnička ulica 12",
          priest: "vlč. Krunoslav Karas",
          purpose: "Kućna sv. Pričest",
          done: false,
          report: "",
        },
        {
          id: "vis2",
          scheduled: addDays(-14),
          type: "obitelj",
          person: "Obitelj Kovač",
          familyId: "fam2",
          address: "Kovačeva ulica 8",
          priest: "vlč. Krunoslav Karas",
          purpose: "Pastoralni posjet — lukno",
          done: true,
          report: "Razgovor o luknu 2025.",
        },
      ],
      cashbook: [
        { id: "cb1", date: addDays(-20), type: "ulaz", category: "lukno", ledger: "plavi", description: "Lukno Horvat 2026", amount: 150, paymentMethod: "gotovina", reportCode: "A-1" },
        { id: "cb2", date: addDays(-15), type: "ulaz", category: "nakane", ledger: "plavi", description: "Stipendiji — siječanj", amount: 180, paymentMethod: "žiro", reportCode: "A-1" },
        { id: "cb3", date: addDays(-5), type: "izlaz", category: "materijal", ledger: "plavi", description: "Materijal za katehezu", amount: 85, paymentMethod: "gotovina", reportCode: "C-1" },
        { id: "cb4", date: addDays(-12), type: "izlaz", category: "nadbiskupija", ledger: "crveni", description: "Nadbiskupiji BIH", amount: 125, paymentMethod: "žiro", reportCode: "D-1" },
      ],
      registryBooks: [
        {
          id: "rk1",
          type: "krštenja",
          title: "Knjiga rođenih i krštenih",
          location: "Župni arhiv — sef",
          lastEntry: addDays(-14),
          lastNo: "2026/12",
          custodian: "vlč. Krunoslav Karas",
          status: "u župi",
          notes: "Kan. 535 §2 · izvadci samo iz knjige",
        },
        {
          id: "rk2",
          type: "vjenčanja",
          title: "Knjiga vjenčanih",
          location: "Župni arhiv — sef",
          lastEntry: "2024-09-12",
          lastNo: "2024/08",
          custodian: "župni ured",
          status: "u župi",
          notes: "",
        },
        {
          id: "rk3",
          type: "umrli",
          title: "Knjiga umrlih",
          location: "Župni arhiv",
          lastEntry: addDays(-1),
          lastNo: "2026/03",
          custodian: "župni ured",
          status: "u župi",
          notes: "",
        },
        {
          id: "rk4",
          type: "krizma",
          title: "Knjiga krizmanika",
          location: "Župni arhiv",
          lastEntry: "2025-05-18",
          lastNo: "2025/41",
          custodian: "župni ured",
          status: "u župi",
          notes: "Digitalna evidencija usklađena s knjigom 2025",
        },
      ],
      pastoralCouncil: {
        established: "2008-09-01",
        lastMeeting: addDays(-30),
        nextMeeting: addDays(7),
        members: [
          { id: "zpv1", name: "vlč. Krunoslav Karas", role: "župnik / predsjednik", confirmed: true },
          { id: "zpv2", name: "Ana Horvat", role: "laik — predstavnik", confirmed: true },
          { id: "zpv3", name: "Marija Kovač", role: "kateheta", confirmed: true },
          { id: "zpv4", name: "Ivan Perić", role: "laik", confirmed: true },
          { id: "zpv5", name: "Petar Novak", role: "laik", confirmed: true },
          { id: "zpv6", name: "Josip Marić", role: "laik — ŽEV", confirmed: true },
          { id: "zpv7", name: "Marta Burić", role: "laik", confirmed: false },
        ],
      },
      economicCouncil: {
        budgetYear: 2026,
        lastReview: addDays(-60),
        nextReview: addDays(5),
        members: [
          { id: "zev1", name: "Josip Marić", role: "predsjednik", confirmed: true },
          { id: "zev2", name: "Ana Horvat", role: "član", confirmed: true },
          { id: "zev3", name: "Marko Babić", role: "član", confirmed: true },
        ],
      },
      parishDecree: {
        name: "Župa Blažene Djevice Marije",
        established: "—",
        territory: "Slavonski Brod (centar)",
        decreeRef: "Prema kan. 515–519 · II. sinoda đ.-srij. 2008",
      },
      appGroups: [],
      appUsers: [],
      parishPriests: [],
    };
  }

  function seedFamiliesIfMissing(data) {
    if (Array.isArray(data.families) && data.families.length) return data;
    const streets = data.streets?.length
      ? data.streets
      : [{ id: "st0", name: "Nepoznata ulica", zone: "—", sortOrder: 99, notes: "" }];
    if (!data.streets?.length) data.streets = streets;
    const byFamily = {};
    (data.parishioners || []).forEach((p) => {
      const key = p.family || "Obitelj";
      if (!byFamily[key]) {
        byFamily[key] = {
          id: `fam_${key.toLowerCase()}`,
          surname: key,
          streetId: streets[0].id,
          address: "",
          phone: p.phone || "",
          email: p.email || "",
          status: "aktivna",
          preferredMass: "",
          pastoralNotes: "",
          lastVisit: "",
          tags: [],
          members: [],
        };
      }
      byFamily[key].members.push({
        id: p.id,
        name: p.name,
        birthYear: "",
        relation: "",
        sacraments: [],
        roles: p.roles || [],
        notes: "",
      });
    });
    data.families = Object.values(byFamily);
    return data;
  }

  function migrate(data) {
    if (!Array.isArray(data.publicSubmissions)) data.publicSubmissions = [];
    if (!data.streets?.length) data.streets = defaultData().streets;
    seedFamiliesIfMissing(data);
    (data.families || []).forEach((fam) => {
      if (!Array.isArray(fam.contributions)) fam.contributions = [];
    });
    if (global.PastoralFamilyCrud) global.PastoralFamilyCrud.migrateAllFamilies(data);
    if (data.luknoDefaultAmount == null) data.luknoDefaultAmount = 150;
    if (!Array.isArray(data.visits)) data.visits = defaultData().visits || [];
    if (!Array.isArray(data.cashbook)) data.cashbook = defaultData().cashbook || [];
    if (global.PastoralVisits) global.PastoralVisits.migrate(data);
    if (global.PastoralCashbook) global.PastoralCashbook.migrate(data);
    if (global.PastoralMessages) global.PastoralMessages.migrate(data);
    if (global.PastoralPreparation) global.PastoralPreparation.migrateAll(data);
    data.intentions?.forEach((n) => {
      if (n.paid && !n.paymentId) n.paymentId = n.paymentId || "LEGACY-PAID";
    });
    const touchStipend = (arr) => {
      (arr || []).forEach((r) => {
        if (r.stipend == null) r.stipend = 0;
        if (r.stipendPaid == null) r.stipendPaid = r.stipend === 0;
        if (!r.stipendPaidAt) r.stipendPaidAt = "";
      });
    };
    touchStipend(data.baptisms);
    touchStipend(data.weddings);
    touchStipend(data.funerals);
    touchStipend(data.anointing);
    (data.firstCommunion || []).forEach((g) => {
      if (g.groupFee == null) g.groupFee = 0;
      if (g.groupFeePaid == null) g.groupFeePaid = g.groupFee === 0;
    });
    (data.confirmations || []).forEach((g) => {
      if (g.groupFee == null) g.groupFee = 0;
      if (g.groupFeePaid == null) g.groupFeePaid = g.groupFee === 0;
    });
    if (!Array.isArray(data.parishDebts)) data.parishDebts = [];
    if (!Array.isArray(data.invoices)) data.invoices = [];
    if (global.PastoralInvoices) global.PastoralInvoices.migrate(data);
    if (!Array.isArray(data.registryBooks)) data.registryBooks = defaultData().registryBooks || [];
    if (!data.pastoralCouncil?.members?.length) data.pastoralCouncil = defaultData().pastoralCouncil;
    if (!data.economicCouncil?.members?.length) data.economicCouncil = defaultData().economicCouncil;
    if (!data.parishDecree) data.parishDecree = defaultData().parishDecree;
    if (global.PastoralFinanceAdv) global.PastoralFinanceAdv.migrate(data);
    if (global.PastoralStaffMessages) global.PastoralStaffMessages.migrate(data);
    if (global.PastoralAdminDocs) global.PastoralAdminDocs.migrate(data);
    if (global.PastoralZupniListic) {
      const settings = global.PastoralParish?.loadSettings?.() || {};
      global.PastoralZupniListic.migrate(data, settings);
    }
    (data.families || []).forEach((f) => {
      if (global.PastoralFamilyList) global.PastoralFamilyList.migrateFamily(f);
    });
    if (global.PastoralPermissions) global.PastoralPermissions.migrate(data);
    return data;
  }

  function load() {
    try {
      const r = localStorage.getItem(KEY);
      if (r) return migrate(JSON.parse(r));
    } catch (_) {}
    const d = defaultData();
    save(d);
    return d;
  }

  function save(data) {
    localStorage.setItem(KEY, JSON.stringify(data));
  }

  function ensureSeed() {
    if (!localStorage.getItem(KEY)) save(defaultData());
  }

  global.PastoralData = { load, save, ensureSeed, defaultData, addDays };
})(typeof window !== "undefined" ? window : global);
