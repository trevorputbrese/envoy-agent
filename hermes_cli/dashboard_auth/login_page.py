"""Server-rendered /login page (no React, no SPA bundle, no injected token).

Providers come from the registry; an OAuth provider renders an anchor to
``/auth/login?provider=<name>``, a ``supports_password`` provider renders a
credential form wired by :data:`_PASSWORD_FORM_SCRIPT`. Styling follows the
dashboard's Clarity theme; fonts load from the SPA's ``/fonts/`` mount, which the gate
allowlists pre-auth.

The ``class="provider-btn"`` anchor is test-stable: the suite extracts its
href to walk the OAuth flow.
"""
from __future__ import annotations

import html
from urllib.parse import quote, urlencode

from hermes_cli.dashboard_auth import list_interactive_providers, list_session_providers

# Single curly braces are ``str.format`` placeholders; CSS curlies are doubled.
_LOGIN_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in — Envoy Agent</title>
<style>
  /* VMware Clarity look, matching the dashboard's default theme: navy header bar, light
     page, white card, action-blue buttons. Metropolis (Clarity's typeface) is the same file the
     SPA loads from its /fonts/ mount, which the gate allowlists pre-auth. */
  @font-face {{
    font-family: 'Metropolis';
    font-style: normal;
    font-weight: 300;
    font-display: swap;
    src: url('/fonts/Metropolis-Light.woff') format('woff');
  }}
  @font-face {{
    font-family: 'Metropolis';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/Metropolis-Regular.woff') format('woff');
  }}
  @font-face {{
    font-family: 'Metropolis';
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url('/fonts/Metropolis-SemiBold.woff') format('woff');
  }}
  :root {{
    --clr-header: #00364d;
    --clr-page: #f4f6f7;
    --clr-card: #ffffff;
    --clr-ink: #21333b;
    --clr-muted: #565656;
    --clr-border: #cccccc;
    --clr-action: #006a91;
    --clr-action-hover: #004d8a;
    --clr-danger: #c21d00;
  }}

  *, *::before, *::after {{ box-sizing: border-box; }}

  html, body {{
    margin: 0;
    padding: 0;
    min-height: 100%;
    background: var(--clr-page);
    color: var(--clr-ink);
    font-family: Metropolis, "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}

  .header {{
    display: flex;
    align-items: center;
    height: 3.75rem;
    padding: 0 1.5rem;
    background: var(--clr-header);
    color: #ffffff;
  }}
  .brand {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.15rem;
    font-weight: 500;
    letter-spacing: 0.01em;
  }}
  .brand .mark {{ color: #70c7ec; font-size: 1.35rem; line-height: 1; }}
  .brand .product {{
    padding-left: 0.6rem;
    border-left: 1px solid rgba(255, 255, 255, 0.35);
    font-weight: 400;
    color: rgba(255, 255, 255, 0.8);
  }}

  main {{
    width: 100%;
    max-width: 26rem;
    margin: clamp(2rem, 10vh, 7rem) auto 2rem;
    padding: 0 1rem;
  }}

  .card {{
    padding: 2rem 1.75rem 1.75rem;
    background: var(--clr-card);
    border: 1px solid var(--clr-border);
    border-radius: 3px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  }}

  h1 {{
    margin: 0 0 0.35rem;
    font-size: 1.6rem;
    font-weight: 300;
    color: var(--clr-ink);
  }}

  .subtitle {{
    margin: 0 0 1.5rem;
    color: var(--clr-muted);
  }}

  .provider-list {{
    display: grid;
    gap: 0.75rem;
  }}

  /* Clarity primary button. */
  .provider-btn {{
    display: block;
    width: 100%;
    padding: 0.6rem 1rem;
    text-align: center;
    background: var(--clr-action);
    color: #ffffff;
    font: inherit;
    font-weight: 600;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    text-decoration: none;
    border: 1px solid var(--clr-action);
    border-radius: 3px;
    cursor: pointer;
    transition: background 0.12s ease-out;
  }}
  .provider-btn:hover {{ background: var(--clr-action-hover); border-color: var(--clr-action-hover); }}
  .provider-btn:focus-visible {{ outline: 2px solid var(--clr-action); outline-offset: 2px; }}

  .provider-form {{
    display: grid;
    gap: 0.9rem;
    text-align: left;
  }}
  .form-title {{
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--clr-muted);
  }}
  .field {{
    display: grid;
    gap: 0.25rem;
  }}
  .field-label {{
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--clr-ink);
  }}
  /* Clarity form control: bottom-border input. */
  .field-input {{
    width: 100%;
    padding: 0.4rem 0.1rem;
    background: transparent;
    color: var(--clr-ink);
    border: 0;
    border-bottom: 1px solid #b3b3b3;
    border-radius: 0;
    font: inherit;
  }}
  .field-input:focus-visible {{
    outline: none;
    border-bottom: 2px solid var(--clr-action);
  }}
  .form-error {{
    color: var(--clr-danger);
    font-size: 0.8rem;
  }}
  .provider-form .provider-btn {{ margin-top: 0.5rem; }}

  footer {{
    margin-top: 1.25rem;
    text-align: center;
    color: var(--clr-muted);
    font-size: 0.75rem;
  }}
  footer .sep {{ display: none; }}

  ::selection {{ background: #c5eeff; color: var(--clr-ink); }}
</style>
</head>
<body>
<header class="header">
  <div class="brand"><span class="mark">&#9672;</span>Envoy<span class="product">Agent</span></div>
</header>
<main>
  <div class="card">
    <h1>Sign in</h1>
    <p class="subtitle">Choose a sign-in method to continue to the Envoy Agent dashboard.</p>
    <div class="provider-list">
{provider_buttons}
    </div>
  </div>
  <footer>
    <span class="sep"></span>Public bind &middot; Auth required<span class="sep"></span>
  </footer>
</main>
{password_script}
</body>
</html>
"""

_EMPTY_HTML = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign-in unavailable — Envoy Agent</title>
<style>
  @font-face {
    font-family: 'Metropolis';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/Metropolis-Regular.woff') format('woff');
  }
  @font-face {
    font-family: 'Metropolis';
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url('/fonts/Metropolis-SemiBold.woff') format('woff');
  }
  :root {
    --background-base: #1b2a32;
    --midground: #70c7ec;
    --foreground: #ffffff;
    --hairline: color-mix(in srgb, #70c7ec 25%, transparent);
  }
  *, *::before, *::after { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; min-height: 100%;
    background: var(--background-base);
    color: var(--foreground);
    font-family: Metropolis, "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    font-size: 16px; line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }
  body {
    display: grid; place-items: center;
    padding: clamp(1.5rem, 6vh, 6rem) 1.25rem;
  }
  main {
    width: 100%; max-width: 32rem;
    padding: 2.25rem 2rem;
    background: color-mix(in srgb, #ffffff 2%, var(--background-base));
    border: 1px solid var(--hairline);
    box-shadow:
      inset 1px 1px 0 0 color-mix(in srgb, #ffffff 5%, transparent),
      inset -1px -1px 0 0 rgba(0, 0, 0, 0.4),
      0 24px 60px -20px rgba(0, 0, 0, 0.6);
  }
  h1 {
    margin: 0 0 1rem;
    font-family: inherit;
    font-weight: 600; font-size: 1.5rem;
    letter-spacing: 0.05em; text-transform: uppercase;
    color: var(--midground);
  }
  p { margin: 0 0 1rem; }
  code {
    background: var(--midground);
    color: var(--background-base);
    padding: 0.1em 0.35em;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
  a { color: var(--midground); }
</style>
</head>
<body>
<main>
<h1>Sign-in unavailable</h1>
<p>This dashboard is bound to a non-loopback host but no authentication
providers are available.</p>
<p>Configure the bundled username/password provider or an OAuth provider.
See the <a href="https://github.com/trevorputbrese/envoy-agent/blob/main/website/docs/user-guide/features/web-dashboard.md">dashboard
authentication documentation</a> for setup instructions.</p>
<p>For auth-free local use, bind to <code>127.0.0.1</code> and connect through
an SSH tunnel or Tailscale.</p>
</main>
</body>
</html>
"""

# Token-gated deployment (every registered provider is provisioned-credential-only):
# there is nothing to click, so the page explains the credential channel instead of
# rendering an empty options list. {provider_names} / {note} are pre-escaped HTML.
_TOKEN_MODE_HTML = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Token-gated dashboard — Envoy Agent</title>
<style>
  @font-face {
    font-family: 'Metropolis';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url('/fonts/Metropolis-Regular.woff') format('woff');
  }
  @font-face {
    font-family: 'Metropolis';
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url('/fonts/Metropolis-SemiBold.woff') format('woff');
  }
  :root {
    --background-base: #1b2a32;
    --midground: #70c7ec;
    --foreground: #ffffff;
    --hairline: color-mix(in srgb, #70c7ec 25%, transparent);
  }
  *, *::before, *::after { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; min-height: 100%;
    background: var(--background-base);
    color: var(--foreground);
    font-family: Metropolis, "Avenir Next", "Helvetica Neue", Arial, sans-serif;
    font-size: 16px; line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }
  body {
    display: grid; place-items: center;
    padding: clamp(1.5rem, 6vh, 6rem) 1.25rem;
  }
  main {
    width: 100%; max-width: 32rem;
    padding: 2.25rem 2rem;
    background: color-mix(in srgb, #ffffff 2%, var(--background-base));
    border: 1px solid var(--hairline);
    box-shadow:
      inset 1px 1px 0 0 color-mix(in srgb, #ffffff 5%, transparent),
      inset -1px -1px 0 0 rgba(0, 0, 0, 0.4),
      0 24px 60px -20px rgba(0, 0, 0, 0.6);
  }
  h1 {
    margin: 0 0 1rem;
    font-family: inherit;
    font-weight: 600; font-size: 1.5rem;
    letter-spacing: 0.05em; text-transform: uppercase;
    color: var(--midground);
  }
  p { margin: 0 0 1rem; }
  code {
    background: var(--midground);
    color: var(--background-base);
    padding: 0.1em 0.35em;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }
</style>
</head>
<body>
<main>
<h1>Token-gated dashboard</h1>
<p>This deployment authenticates with a provisioned credential
({provider_names}), not a browser sign-in.</p>
<p>{note}</p>
</main>
</body>
</html>
"""


# Emitted ONLY when a ``supports_password`` provider is listed, so OAuth-only
# login pages stay script-free. Plain string (not ``str.format``): braces are
# literal. One delegated submit handler covers every form; the provider name
# comes from the form's ``data-provider`` attribute.
#
# Reverse-proxy prefix support: the script reads ``data-prefix`` from the
# ``<main>`` element (set by :func:`render_login_html`) and prepends it
# to the POST target and the post-login landing path so the login flow
# works behind ``X-Forwarded-Prefix`` proxies.
_PASSWORD_FORM_SCRIPT = """\
<script>
(function () {
  var mainEl = document.querySelector('main');
  var prefix = (mainEl && mainEl.getAttribute('data-prefix')) || '';
  function handle(form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var err = form.querySelector('.form-error');
      var btn = form.querySelector('button[type=submit]');
      if (err) { err.hidden = true; err.textContent = ''; }
      if (btn) { btn.disabled = true; }
      var body = {
        provider: form.getAttribute('data-provider') || '',
        username: (form.querySelector('input[name=username]') || {}).value || '',
        password: (form.querySelector('input[name=password]') || {}).value || '',
        next: (form.querySelector('input[name=next]') || {}).value || ''
      };
      fetch(prefix + '/auth/password-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        credentials: 'same-origin'
      }).then(function (resp) {
        if (resp.ok) {
          return resp.json().then(function (data) {
            window.location.assign((data && data.next) || (prefix + '/'));
          });
        }
        var msg = resp.status === 429
          ? 'Too many attempts. Please wait and try again.'
          : (resp.status === 401 ? 'Invalid username or password.'
                                 : 'Sign-in failed. Please try again.');
        if (err) { err.textContent = msg; err.hidden = false; }
        if (btn) { btn.disabled = false; }
      }).catch(function () {
        if (err) { err.textContent = 'Network error. Please try again.'; err.hidden = false; }
        if (btn) { btn.disabled = false; }
      });
    });
  }
  var forms = document.querySelectorAll('form.provider-form');
  for (var i = 0; i < forms.length; i++) { handle(forms[i]); }
})();
</script>
"""


def render_login_html(*, next_path: str = "", prefix: str = "") -> str:
    """Return the full HTML for ``GET /login``.

    ``next_path`` is threaded into each provider button/form so the OAuth round
    trip carries it end-to-end. The caller validates it same-origin; it is
    HTML-escaped here as defence in depth.

    ``prefix`` — when set, the path prefix from ``X-Forwarded-Prefix``
    (e.g. ``"/hermes"``). Prepended to all auth URLs so the login page
    works behind a reverse proxy that mounts the dashboard at a
    sub-path. Empty string (default) means no prefix — bare-root
    deploys are unaffected.
    """
    providers = list_session_providers()
    if not providers:
        return _EMPTY_HTML
    # URL-encode then HTML-escape, matching the gate's ``_safe_next_target``
    # shape so a round-tripped value is byte-identical.
    next_qs = f"&next={html.escape(quote(next_path, safe=''), quote=True)}" if next_path else ""
    interactive = list_interactive_providers()
    if not interactive:
        # A deployment authenticated by a provisioned credential (e.g. the
        # session-token provider): there is nothing to click. Say so instead of
        # rendering a page with no sign-in options.
        names = ", ".join(html.escape(p.display_name) for p in providers)
        # str.replace, not str.format: the template's CSS braces are literal.
        return (_TOKEN_MODE_HTML
                .replace("{provider_names}", names)
                .replace("{note}",
                         "Clients authenticate with the deployment&rsquo;s provisioned "
                         "credential (<code>Authorization: Bearer</code>, or "
                         "<code>?token=</code> on the /api/ws upgrade) &mdash; e.g. Envoy "
                         "Desktop&rsquo;s &ldquo;Session token&rdquo; remote-gateway field. "
                         "There is no browser sign-in flow."))
    buttons = [
        _render_password_form(p, next_path, prefix=prefix)
        if getattr(p, "supports_password", False) else
        f'      <a class="provider-btn" '
        f'href="{prefix}/auth/login?provider={html.escape(p.name, quote=True)}{next_qs}">'
        f'Sign in with {html.escape(p.display_name)}</a>'
        for p in interactive
    ]
    needs_password_script = any(getattr(p, "supports_password", False) for p in interactive)
    html_out = _LOGIN_HTML_TEMPLATE.format(
        provider_buttons="\n".join(buttons),
        password_script=_PASSWORD_FORM_SCRIPT if needs_password_script else "",
    )
    # Inject the reverse-proxy prefix so the password-login JS can read
    # it from the <main> element's data attribute, and rewrite the font
    # URLs to stay inside the mount.  ``str.replace`` after ``str.format``
    # avoids interfering with the CSS ``{{ }}`` doubling in the template.
    return _apply_proxy_prefix(html_out, prefix)


def _apply_proxy_prefix(html_out: str, prefix: str) -> str:
    """Rewrite a rendered login-family page for a reverse-proxy sub-path.

    Two rewrites, both no-ops when *prefix* is empty (bare-root deploys are
    byte-for-byte unaffected):

    * ``<main>`` gains ``data-prefix`` so the password-login JS (a plain
      string, never ``str.format``-aware) can prepend the prefix to its
      fetch target and post-login landing.
    * ``@font-face`` ``url('/fonts/...')`` becomes ``url('<prefix>/fonts/...')``
      so the fonts load from the mount instead of the origin root (404
      behind a prefix-stripping proxy).
    """
    if not prefix:
        return html_out
    html_out = html_out.replace("<main>", f'<main data-prefix="{prefix}">', 1)
    html_out = html_out.replace("url('/fonts/", f"url('{prefix}/fonts/")
    return html_out


def render_native_provider_choice_html(
        *, providers, authorize_path: str, code_challenge: str,
        code_challenge_method: str, redirect_uri: str, state: str,
        prefix: str = "") -> str:
    """Provider picker for a native authorize request with more than one interactive provider.

    Every link re-enters ``/auth/native/authorize`` with the SAME desktop PKCE inputs plus an
    explicit ``provider``, so the choice never leaves the validated native flow. ``prefix``
    (from ``X-Forwarded-Prefix``) rewrites the template's font URLs so the page works behind
    a reverse-proxy sub-path; the buttons' ``authorize_path`` is already prefixed by the caller.
    """
    common = {"code_challenge": code_challenge, "code_challenge_method": code_challenge_method,
              "redirect_uri": redirect_uri, "state": state}
    buttons = []
    for p in providers:
        href = html.escape(f"{authorize_path}?{urlencode({**common, 'provider': p.name})}",
                           quote=True)
        buttons.append(f'      <a class="provider-btn" href="{href}">'
                       f'Sign in with {html.escape(p.display_name)}</a>')
    if not buttons:
        return _EMPTY_HTML
    return _apply_proxy_prefix(
        _LOGIN_HTML_TEMPLATE.format(
            provider_buttons="\n".join(buttons), password_script=""),
        prefix)


def _render_password_form(provider, next_path: str, *, prefix: str = "") -> str:
    """Username/password form for a ``supports_password`` provider.

    ``next_path`` rides in a hidden field (already validated by the caller,
    HTML-escaped here). The provider name is a ``data-`` attribute so the
    script does not depend on field ordering.

    ``prefix`` — reverse-proxy path prefix (e.g. ``"/hermes"``); kept for
    interface parity with the other renderers (the submit handler reads
    the prefix from ``<main data-prefix>``).
    """
    pname = html.escape(provider.name, quote=True)
    plabel = html.escape(provider.display_name)
    safe_next = html.escape(next_path, quote=True) if next_path else ""
    return (
        f'      <form class="provider-form" data-provider="{pname}" '
        f'autocomplete="on">\n'
        f'        <div class="form-title">Sign in with {plabel}</div>\n'
        f'        <input type="hidden" name="next" value="{safe_next}">\n'
        f'        <label class="field">\n'
        f'          <span class="field-label">Username</span>\n'
        f'          <input class="field-input" type="text" name="username" '
        f'autocomplete="username" autocapitalize="none" '
        f'autocorrect="off" spellcheck="false" required>\n'
        f'        </label>\n'
        f'        <label class="field">\n'
        f'          <span class="field-label">Password</span>\n'
        f'          <input class="field-input" type="password" name="password" '
        f'autocomplete="current-password" required>\n'
        f'        </label>\n'
        f'        <div class="form-error" role="alert" hidden></div>\n'
        f'        <button class="provider-btn" type="submit">Sign in</button>\n'
        f'      </form>'
    )
