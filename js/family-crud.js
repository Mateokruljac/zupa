/**
 * Obitelji — CRUD, lukno i davanja po godinama
 */
(function (global) {
  const DEFAULT_LUKNO = 150;

  function defaultContribution(year) {
    return {
      id: `yc_${year}_${Date.now().toString(36).slice(2, 5)}`,
      year: Number(year),
      luknoPaid: false,
      luknoAmount: DEFAULT_LUKNO,
      luknoPaidAt: "",
      churchDonation: 0,
      donationDate: "",
      notes: "",
    };
  }

  function ensureContributions(fam) {
    if (!Array.isArray(fam.contributions)) fam.contributions = [];
    return fam;
  }

  function sortContributions(fam) {
    ensureContributions(fam);
    fam.contributions.sort((a, b) => b.year - a.year);
    return fam;
  }

  function getContribution(fam, year) {
    ensureContributions(fam);
    return fam.contributions.find((c) => c.year === Number(year));
  }

  function ensureYear(fam, year) {
    let row = getContribution(fam, year);
    if (!row) {
      row = defaultContribution(year);
      fam.contributions.push(row);
    }
    return row;
  }

  function currentYearStatus(fam, year) {
    const row = getContribution(fam, year || new Date().getFullYear());
    if (!row) return { paid: false, lukno: 0, donation: 0 };
    return {
      paid: !!row.luknoPaid,
      lukno: Number(row.luknoAmount) || 0,
      donation: Number(row.churchDonation) || 0,
    };
  }

  function migrateFamily(fam) {
    ensureContributions(fam);
    if (!fam.contributions.length) {
      const y = new Date().getFullYear();
      [y - 2, y - 1, y].forEach((yr) => fam.contributions.push(defaultContribution(yr)));
    }
    sortContributions(fam);
    return fam;
  }

  function migrateAllFamilies(data) {
    (data.families || []).forEach(migrateFamily);
    return data;
  }

  global.PastoralFamilyCrud = {
    DEFAULT_LUKNO,
    defaultContribution,
    ensureContributions,
    sortContributions,
    getContribution,
    ensureYear,
    currentYearStatus,
    migrateFamily,
    migrateAllFamilies,
  };
})(typeof window !== "undefined" ? window : global);
