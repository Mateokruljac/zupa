/**
 * Grupe, korisnici i dozvole modula (demo — priprema za produkciju)
 */
(function (global) {
  const GROUP_KIND_LABELS = {
    priest: "Svećenici župe",
    staff: "Službenici ureda",
    council: "Vijeća",
    custom: "Prilagođena grupa",
  };

  const MODULES = {
    pregled: {
      label: "Pregled",
      pages: ["dashboard", "admin-paket"],
    },
    zupa: {
      label: "Župa i vjernici",
      pages: ["podsjetnici", "obitelji", "posjete", "ulice"],
    },
    liturgija: {
      label: "Liturgija",
      pages: ["nakane", "mise", "zupni-listic", "sluzitelji"],
    },
    sakramenti: {
      label: "Sakramenti",
      pages: ["krsenja", "prva-pricest", "krizma", "vjencanja", "pogrebi", "pomazanje"],
    },
    financije: {
      label: "Financije",
      pages: ["dugovanja", "racuni", "blagajna", "financijska-izvjestaja"],
    },
    isprave: {
      label: "Isprave i matice",
      pages: ["formulari", "potvrde", "dokumenti", "maticne-knjige"],
    },
    ured: {
      label: "Župni ured",
      pages: ["vijeca", "kalendar", "zadaci", "javne-prijave", "komunikacija", "poruke"],
    },
    postavke: {
      label: "Postavke i sigurnost",
      pages: ["postavke", "sigurnost"],
    },
    korisnici: {
      label: "Korisnici i grupe",
      pages: ["korisnici"],
    },
  };

  const PAGE_TO_MODULE = {};
  Object.entries(MODULES).forEach(([mod, cfg]) => {
    (cfg.pages || []).forEach((p) => {
      PAGE_TO_MODULE[p] = mod;
    });
  });

  const LEGACY_ROLE_GROUP = {
    zupnik: "grp-svecenici",
    vikar: "grp-svecenici",
    upravitelj: "grp-upravitelj",
    kateheta: "grp-kateheta",
  };

  const LEGACY_ROLE_LABELS = {
    zupnik: "Župnik",
    vikar: "Vikar",
    upravitelj: "Upravitelj",
    kateheta: "Kateheta",
  };

  function defaultGroups() {
    return [
      {
        id: "grp-svecenici",
        slug: "svecenici",
        name: "Svećenici župe",
        kind: "priest",
        description: "Župnik, vikar i svećenici — pastoralni i administrativni pristup po dogovoru.",
        permissions: Object.keys(MODULES),
        isSystem: true,
      },
      {
        id: "grp-upravitelj",
        slug: "upravitelj",
        name: "Župni upravitelj",
        kind: "staff",
        description: "Financije, nakane, obitelji — bez matičnih knjiga i postavki sustava.",
        permissions: ["pregled", "zupa", "liturgija", "financije", "ured", "isprave"],
        isSystem: true,
      },
      {
        id: "grp-kateheta",
        slug: "kateheta",
        name: "Katehete i suradnici",
        kind: "staff",
        description: "Sakramenti, obitelji, podsjetnici — bez blagajne i postavki.",
        permissions: ["pregled", "zupa", "sakramenti", "ured"],
        isSystem: true,
      },
      {
        id: "grp-zpv",
        slug: "zpv",
        name: "Župno pastoralno vijeće",
        kind: "council",
        description: "Pregled i pastoralni moduli (bez financija).",
        permissions: ["pregled", "zupa", "ured"],
        isSystem: false,
      },
      {
        id: "grp-zev",
        slug: "zev",
        name: "Župno ekonomsko vijeće",
        kind: "council",
        description: "Pregled i financije.",
        permissions: ["pregled", "financije", "ured"],
        isSystem: false,
      },
    ];
  }

  function defaultPriestsAndUsers(settings) {
    const pastor = settings?.pastor || "vlč. Krunoslav Karas";
    const email = settings?.email || "ured@zupa-bdm-sb.hr";
    const phone = settings?.phone || "";
    return {
      parishPriests: [
        {
          id: "pr1",
          name: pastor,
          title: "župnik",
          email,
          phone,
          active: true,
          userId: "usr1",
          notes: "Župnik župe",
        },
        {
          id: "pr2",
          name: "don Josip Novak",
          title: "vikar",
          email: "vikar@zupa-bdm-sb.hr",
          phone: "098 111 2222",
          active: true,
          userId: "usr2",
          notes: "",
        },
      ],
      appUsers: [
        {
          id: "usr1",
          name: pastor,
          email,
          groupIds: ["grp-svecenici"],
          active: true,
          priestId: "pr1",
          legacyRole: "zupnik",
        },
        {
          id: "usr2",
          name: "don Josip Novak",
          email: "vikar@zupa-bdm-sb.hr",
          groupIds: ["grp-svecenici"],
          active: true,
          priestId: "pr2",
          legacyRole: "vikar",
        },
        {
          id: "usr3",
          name: "Ana Marić",
          email: "kateheta@zupa-bdm-sb.hr",
          groupIds: ["grp-kateheta"],
          active: true,
          priestId: null,
          legacyRole: "kateheta",
        },
        {
          id: "usr4",
          name: "Josip Marić",
          email: "upravitelj@zupa-bdm-sb.hr",
          groupIds: ["grp-upravitelj"],
          active: true,
          priestId: null,
          legacyRole: "upravitelj",
        },
      ],
    };
  }

  function migrate(data) {
    const settings = global.PastoralParish?.loadSettings?.() || {};
    if (!Array.isArray(data.appGroups) || !data.appGroups.length) {
      data.appGroups = defaultGroups();
    }
    if (!Array.isArray(data.parishPriests) || !data.parishPriests.length) {
      const seed = defaultPriestsAndUsers(settings);
      data.parishPriests = seed.parishPriests;
      if (!data.appUsers?.length) data.appUsers = seed.appUsers;
    }
    if (!Array.isArray(data.appUsers)) data.appUsers = [];
    return data;
  }

  function navFileToPageId(file) {
    const f = String(file || "");
    if (f === "app.html" || f === "app") return "dashboard";
    const base = f.replace(/^\/?pages\//, "").replace(/\.html$/, "");
    return base || "dashboard";
  }

  function resolveGroups(data, groupIds) {
    const ids = groupIds || [];
    return (data.appGroups || []).filter((g) => ids.includes(g.id));
  }

  function permissionsFromGroups(data, groupIds) {
    const set = new Set();
    resolveGroups(data, groupIds).forEach((g) => {
      (g.permissions || []).forEach((p) => set.add(p));
    });
    return [...set];
  }

  function buildSessionPayload({ email, legacyRole, data }) {
    const d = migrate(data || global.PastoralData?.load?.() || {});
    const normalizedEmail = String(email || "").trim().toLowerCase();
    const user = (d.appUsers || []).find(
      (u) => u.active !== false && String(u.email || "").trim().toLowerCase() === normalizedEmail
    );

    let groupIds = user?.groupIds?.length ? [...user.groupIds] : [];
    if (!groupIds.length && legacyRole) {
      const gid = LEGACY_ROLE_GROUP[legacyRole];
      if (gid) groupIds = [gid];
    }
    if (!groupIds.length) groupIds = ["grp-kateheta"];

    const groups = resolveGroups(d, groupIds);
    const permissions = permissionsFromGroups(d, groupIds);
    const isPriest = groupIds.includes("grp-svecenici") || groups.some((g) => g.kind === "priest");

    let roleLabel = LEGACY_ROLE_LABELS[legacyRole] || legacyRole || "Korisnik";
    if (user?.priestId) {
      const pr = (d.parishPriests || []).find((p) => p.id === user.priestId);
      if (pr?.title) roleLabel = `${pr.title} · ${groups.map((g) => g.name).join(", ")}`;
      else if (groups.length) roleLabel = groups.map((g) => g.name).join(", ");
    } else if (groups.length) {
      roleLabel = groups.map((g) => g.name).join(", ");
    }

    return {
      email: user?.email || email,
      userId: user?.id || null,
      userName: user?.name || null,
      priestId: user?.priestId || null,
      legacyRole: user?.legacyRole || legacyRole || null,
      groupIds,
      groups: groups.map((g) => ({ id: g.id, name: g.name, kind: g.kind, slug: g.slug })),
      permissions,
      isPriest,
      roleLabel,
    };
  }

  function sessionFromStorage() {
    try {
      const raw = localStorage.getItem(global.PastoralParish?.SESSION_KEY || "pastoral_session");
      if (!raw) return null;
      const s = JSON.parse(raw);
      if (s.expiresAt && Date.now() > s.expiresAt) return null;
      return s;
    } catch {
      return null;
    }
  }

  function canAccessModule(session, moduleKey) {
    if (!session?.permissions?.length) return true;
    return session.permissions.includes(moduleKey);
  }

  function canAccessPage(pageId, session) {
    const sess = session || sessionFromStorage();
    if (!sess) return false;
    if (pageId === "login" || pageId === "index") return true;
    const mod = PAGE_TO_MODULE[pageId];
    if (!mod) return true;
    return canAccessModule(sess, mod);
  }

  function filterNav(navItems, session) {
    const sess = session || sessionFromStorage();
    if (!sess?.permissions?.length) return navItems;

    const out = [];
    let pendingLabel = null;

    navItems.forEach((item) => {
      if (item.type === "label") {
        pendingLabel = item;
        return;
      }
      const pageId = navFileToPageId(item[0]);
      const mod = PAGE_TO_MODULE[pageId];
      if (!mod || canAccessModule(sess, mod)) {
        if (pendingLabel) {
          out.push(pendingLabel);
          pendingLabel = null;
        }
        out.push(item);
      }
    });
    return out;
  }

  function getParishPriests(data, opts = {}) {
    const list = (data?.parishPriests || []).filter((p) => p.active !== false);
    if (opts.activeOnly === false) return data?.parishPriests || [];
    return list;
  }

  function findUserByEmail(data, email) {
    const e = String(email || "").trim().toLowerCase();
    return (data?.appUsers || []).find((u) => String(u.email || "").trim().toLowerCase() === e);
  }

  global.PastoralPermissions = {
    MODULES,
    PAGE_TO_MODULE,
    GROUP_KIND_LABELS,
    LEGACY_ROLE_GROUP,
    LEGACY_ROLE_LABELS,
    defaultGroups,
    migrate,
    navFileToPageId,
    buildSessionPayload,
    sessionFromStorage,
    canAccessModule,
    canAccessPage,
    filterNav,
    getParishPriests,
    findUserByEmail,
    permissionsFromGroups,
    resolveGroups,
  };
})(typeof window !== "undefined" ? window : global);
