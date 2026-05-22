/**
 * Gregorijanske nakane — 30 uzastopnih misa
 */
(function (global) {
  function createSeries(data, fields) {
    const seriesId = `greg_${Date.now().toString(36).slice(2, 8)}`;
    const start = new Date(fields.startDate + "T12:00:00");
    for (let i = 0; i < 30; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      const iso = d.toISOString().slice(0, 10);
      data.intentions.push({
        id: `n_${seriesId}_${i}`,
        date: iso,
        massTime: fields.massTime || "18:00",
        intentionFor: fields.intentionFor,
        requestedBy: fields.requestedBy || "",
        stipend: Number(fields.stipend) || 0,
        paid: false,
        paymentId: "",
        paidAt: "",
        notes: `Gregorijanska serija — ${i + 1}/30`,
        gregorianSeriesId: seriesId,
        gregorianDay: i + 1,
      });
    }
    return seriesId;
  }

  global.PastoralGregorian = { createSeries };
})(typeof window !== "undefined" ? window : global);
