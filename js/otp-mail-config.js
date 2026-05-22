/**
 * OTP e-mail — Netlify Functions (preporučeno) ili EmailJS
 * Upute: README.md → „OTP prijava / Netlify“
 */
(function (global) {
  global.PastoralOtpMailConfig = {
    otpRecipient: "mateokruljac123@gmail.com",

    /**
     * netlify — poziva /.netlify/functions/send-otp (simulacija ili Resend)
     * emailjs — slanje iz preglednika (treba ključeve)
     * auto   — netlify na netlify.app / localhost:8888, inače emailjs ili demo
     */
    provider: "netlify",

    /** URL funkcije (prazno = automatski) */
    netlifyFunctionUrl: "",

    /** Lokalno: `npm run dev` (netlify dev na :8888) umjesto samo serve */
    useNetlifyDevLocally: true,

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
