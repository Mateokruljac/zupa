/**
 * Putanje — Django server, lokalni static server ili file:// (demo)
 */
(function (global) {
  function isDjango() {
    const p = location.pathname;
    return (
      p === "/" ||
      p === "/login/" ||
      p === "/app/" ||
      p.startsWith("/pages/") ||
      p.startsWith("/public/") ||
      p === "/login.html" ||
      p === "/app.html"
    );
  }

  function djangoPageUrl(file) {
    const clean = String(file).replace(/^\/?pages\//, "").replace(/^\/?public\//, "").replace(/\.html$/, "");
    if (file.startsWith("public/") || file === "public/index.html") {
      if (clean === "index") return "/public/";
      return `/public/${clean}/`;
    }
    if (clean === "app" || clean === "app.html") return "/app/";
    if (clean === "login" || clean === "login.html") return "/login/";
    return `/pages/${clean}/`;
  }

  function projectRoot() {
    if (isDjango()) return "/static/";
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
    if (isDjango()) return `/static/${clean}`;
    const root = projectRoot();
    if (root) return root + clean;
    if (location.pathname.includes("/pages/")) return `../${clean}`;
    if (location.pathname.includes("/public/")) return `../${clean}`;
    return clean;
  }

  function publicPage(file) {
    if (isDjango()) return djangoPageUrl(file.startsWith("public/") ? file : `public/${file}`);
    return asset(`public/${file}`);
  }

  function adminPage(file) {
    if (isDjango()) return djangoPageUrl(file);
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
    isDjango,
    isFileProtocol,
    needsLocalServer,
  };
})(typeof window !== "undefined" ? window : global);
