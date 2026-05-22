/**
 * OTP e-mail — Netlify Functions (preporučeno) ili EmailJS
 * Upute: README.md → „OTP prijava / Netlify“
 */
(function (global) {
  global.PastoralOtpMailConfig = {
    otpRecipient: "mateokruljac123@gmail.com",

    /**
     * demo — kod se uvijek prikazuje na portalu (preporučeno dok Netlify ne radi)
     * netlify / emailjs / auto — opcionalno u pozadini
     */
    provider: "demo",

    /** Uvijek prikaži OTP na stranici prijave */
    demoAlwaysShowOnPortal: true,

    netlifyFunctionUrl: "",
    useNetlifyDevLocally: false,

    emailjs: {
      publicKey: "",
      serviceId: "",
      templateId: "",
    },

    otpLength: 6,
    otpTtlMinutes: 10,
    maxAttempts: 5,
    resendCooldownSeconds: 60,

    /** Fallback ako ni Netlify ni EmailJS nisu dostupni */
    demoShowCodeWhenNoEmailjs: true,
  };
})(typeof window !== "undefined" ? window : global);
