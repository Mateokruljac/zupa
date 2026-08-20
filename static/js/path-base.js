/**
 * Django putanje aplikacijskih stranica i statičkih datoteka.
 */
(function (global) {
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

  function asset(rel) {
    const clean = String(rel).replace(/^\//, "");
    return `/static/${clean}`;
  }

  function adminPage(file) {
    return djangoPageUrl(file);
  }

  global.PastoralBase = {
    asset,
    adminPage,
  };
})(typeof window !== "undefined" ? window : global);
