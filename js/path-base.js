/**
 * Putanje — radi i preko lokalnog servera i file:// (demo)
 */
(function (global) {
  function projectRoot() {
    const href = decodeURI(location.href).replace(/\\/g, "/");
    const pub = href.indexOf("/public/");
    if (pub >= 0) return href.slice(0, pub + 1);
    const pages = href.indexOf("/pages/");
    if (pages >= 0) return href.slice(0, pages + 1);
    if (/\/(app\.html|login\.html)$/i.test(href)) return href.replace(/\/[^/]+$/, "/");
    return null;
  }

  function asset(rel) {
    const clean = String(rel).replace(/^\//, "");
    const root = projectRoot();
    if (root) return root + clean;
    if (location.pathname.includes("/pages/")) return `../${clean}`;
    if (location.pathname.includes("/public/")) return `../${clean}`;
    return clean;
  }

  function publicPage(file) {
    return asset(`public/${file}`);
  }

  function adminPage(file) {
    const clean = String(file).replace(/^\/?pages\//, "").replace(/^\/?/, "");
    if (clean === "app.html" || clean === "app") return asset("app.html");
    if (clean === "login.html" || clean === "login") return asset("login.html");
    return asset(`pages/${clean}`);
  }

  function isFileProtocol() {
    return location.protocol === "file:";
  }

  function needsLocalServer() {
    return isFileProtocol() && !projectRoot();
  }

  global.PastoralBase = {
    projectRoot,
    asset,
    publicPage,
    adminPage,
    isFileProtocol,
    needsLocalServer,
  };
})(typeof window !== "undefined" ? window : global);
