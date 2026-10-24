/* LibreGol TV — Lightweight GDPR/CCPA Cookie Consent Manager (Zero-dependency) */
(function() {
  var CONSENT_KEY = 'libregol_cookie_consent';
  
  if (localStorage.getItem(CONSENT_KEY)) {
    return; // User already chose
  }

  function initBanner() {
    var isSubdir = window.location.pathname.indexOf('/legal/') !== -1 || 
                   window.location.pathname.indexOf('/canales/') !== -1 || 
                   window.location.pathname.indexOf('/articulos/') !== -1 || 
                   window.location.pathname.indexOf('/partidos/') !== -1;
    var privacyHref = isSubdir ? '../legal/politica-de-privacidad.html' : 'legal/politica-de-privacidad.html';

    var banner = document.createElement('div');
    banner.id = 'libregol-cookie-banner';
    banner.className = 'cookie-consent-bar';
    banner.innerHTML = [
      '<div class="cookie-consent-inner">',
        '<div class="cookie-consent-text">',
          '<span>🍪</span>',
          '<p>Utilizamos cookies técnicas y de análisis para optimizar tu experiencia y ofrecer contenidos deportivos relevantes conforme a nuestra <a href="' + privacyHref + '">Política de Privacidad</a>.</p>',
        '</div>',
        '<div class="cookie-consent-actions">',
          '<button id="btn-cookie-reject" class="cookie-btn cookie-btn-reject">Rechazar</button>',
          '<button id="btn-cookie-accept" class="cookie-btn cookie-btn-accept">Aceptar todas</button>',
        '</div>',
      '</div>'
    ].join('');

    document.body.appendChild(banner);

    document.getElementById('btn-cookie-accept').addEventListener('click', function() {
      localStorage.setItem(CONSENT_KEY, 'accepted');
      closeBanner(banner);
    });

    document.getElementById('btn-cookie-reject').addEventListener('click', function() {
      localStorage.setItem(CONSENT_KEY, 'rejected');
      closeBanner(banner);
    });
  }

  function closeBanner(el) {
    el.style.opacity = '0';
    el.style.transform = 'translateY(100%)';
    setTimeout(function() {
      if (el.parentNode) {
        el.parentNode.removeChild(el);
      }
    }, 300);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBanner);
  } else {
    initBanner();
  }
})();
