# Sargamle — Feature Details

Per-feature specs for planned work. To-do index: [TODO.md](TODO.md).

Template per feature: **Summary · Motivation · Behaviour · Acceptance/Verification · Open questions**.

---

## F1 — GA4 Analytics

**Status:** todo (record-only; not yet implemented)
> **Note:** F2 supersedes F1's "load `gtag.js` automatically in `<head>` on every page load" model with an **opt-in consent** model. If F1 and F2 are implemented together, use F2's consent-gated loading — do **not** ship the always-on `<head>` tag. F1's events/helper/params are unchanged.

### Summary

Add Google Analytics 4 tracking to `sargamle.html` via the official `gtag.js` tag plus a small set of custom game events. Single static file on GitHub Pages (`https://kmcodes.github.io/AIFun/sargamle.html`). No backend, framework, package, build step, new files, or analytics library other than `gtag.js`.

Placeholder Measurement ID used throughout: **`G-XXXXXXXXXX`** — stored in one clearly marked constant/config location so it can be swapped later.

### Motivation

Understand real usage without collecting PII: how many people open the page, how many actually play, completion / win-loss rates, attempts used, share and replay behaviour, and daily-vs-practice / raga split.

**Privacy hard rule:** never send the hidden tune, the player's guesses, IPs, names, emails, or any other PII as event parameters.

### Behaviour

#### GA4 tag

Standard `gtag.js` snippet in `<head>`; keep automatic `page_view`. Do **not** load the external script at all when analytics is disabled (if it can be done cleanly); otherwise ensure no events are sent.

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

#### Disable / dev guard

```javascript
const ANALYTICS_DISABLED =
  location.protocol === 'file:' ||
  location.hostname === 'localhost' ||
  location.hostname === '127.0.0.1' ||
  localStorage.getItem('disable_sargamle_analytics') === 'true';
```

#### Helper

```javascript
trackSargamleEvent(eventName, parameters = {})
```

- Returns safely when `ANALYTICS_DISABLED`.
- Returns safely if `gtag` not loaded.
- Wrapped in try/catch — never interrupts or breaks gameplay.
- Merges common params into every relevant event.

Common params (drawn from existing app state, no duplicate state):

```javascript
{
  game_name: 'sargamle',
  raga: 'bhupali' | 'shuddha_saptak',
  game_mode: 'daily' | 'practice',
  puzzle_number: number
}
```

#### Per-puzzle analytics state

```javascript
let analyticsGameStarted = false;
let analyticsGameCompleted = false;
let analyticsReplayCount = 0;
```

Reset **only** on a genuinely new playable puzzle: new practice puzzle, switch to a different raga's daily puzzle, or any flow creating a new puzzle. Do **not** reset on ordinary render, resize, replay, or restoring the same puzzle from local storage.

#### Events

| Event | Fires when | Params | Notes |
|-------|-----------|--------|-------|
| `game_start` | First meaningful interaction with a puzzle: plays/replays the tune, OR presses a swara pad / mapped key. Once per puzzle session. | `raga, game_mode, puzzle_number` | New practice puzzle after finishing one → new `game_start`. |
| `melody_replay` | Player replays the hidden melody. | `replay_count` | Don't count initial auto-playback unless player triggered it. |
| `guess_submit` | After a valid 5-swara guess is submitted. | `attempt_number, is_correct` | Never send swaras/answer. Don't fire on incomplete/invalid Enter. |
| `game_complete` | Exactly once when puzzle finishes (win or attempts exhausted), in the current session only. | `result: 'won'\|'lost', won, attempts_used, replay_count` | Restoring a completed daily from local storage must NOT re-fire. |
| `share` | Share/copy succeeds. | `method: 'web_share'\|'clipboard'\|'fallback', result, attempts_used` | Only after success; cancelled Web Share ≠ success. |
| `practice_start` | Player explicitly starts a new practice puzzle. | `raga` | May also trigger its own `game_start` on first interaction. |
| `raga_change` | Player switches raga. | `previous_raga, selected_raga` | Not during initial restore of saved/default raga. |

#### GA4 compatibility

Lowercase event names with underscores. Only string / number / boolean param values — no nested objects or arrays. Don't misuse reserved GA4 names. Brief comment near each tracking call naming the user action that triggers it.

#### Debug mode

`localStorage.setItem('sargamle_analytics_debug', 'true')`:
- Log each proposed event + params: `console.debug('[Sargamle Analytics]', eventName, eventParameters);`
- Add `debug_mode: true` to events sent to GA4.
- No gameplay change.

#### Constraints

Do not alter existing gameplay, random generation, daily seed, scoring, keyboard controls, local-storage format, audio, visual design, or share text — except to attach analytics handlers. Use existing app variables/functions rather than duplicating state.

### Acceptance / Verification

1. Production page load sends a normal `page_view`.
2. Replaying the melody twice → one `game_start` + two `melody_replay`.
3. Pressing a swara before replaying → one `game_start`.
4. Incomplete guess submit → no `guess_submit`.
5. Every valid submitted guess → one `guess_submit`.
6. Win → one `game_complete` with `result: 'won'`.
7. Loss → one `game_complete` with `result: 'lost'`.
8. Restoring a completed daily → no duplicate `game_complete`.
9. Successful copy → one `share`.
10. Cancelled native share dialog → no successful `share`.
11. New practice puzzle → per-puzzle analytics state reset.
12. No events on localhost / `127.0.0.1` / `file://`.
13. `disable_sargamle_analytics = 'true'` disables all tracking.
14. Analytics failure never blocks play / submit / complete / share.

### Deliverables for the implementing session

1. Concise summary of changes.
2. Exact place(s) where `G-XXXXXXXXXX` must be replaced.
3. List of implemented events + params.
4. How to enable debug mode.
5. Assumptions about existing variable/function names.
6. Confirmation no answer melodies or player guesses are sent to GA4.

### Open questions

- **Raga naming (resolved).** The original spec said `'bhupali' | 'bilawal'`, but the second raga was renamed in the UI to **"Shuddha Saptak"** (internal `RAGAS[1].name === "Shuddha Saptak"`). GA4 `raga` values are **`'bhupali' | 'shuddha_saptak'`**. Map from `raga.name` at implementation time (e.g. lowercase + underscore the name, or a small lookup) rather than hardcoding by index.
- **`game_start` / auto-play (resolved).** The page does **not** auto-play any tune on load — the tune plays only on explicit "HEAR THE TUNE" / spacebar / pad press. So no special-casing is needed: the first explicit play, replay, or pad/key press is a genuine `game_start`, and the spec's "don't count initial automatic playback as a replay" clause is just a safeguard (currently a no-op).
- Existing state to reuse (verify at implementation time): `ragaIdx`, `raga`, `daily`, `guesses`, `done`, `today`, and `newGame()` as the puzzle-load reset point.

---

## F2 — Privacy controls, consent banner, Privacy Notice & Terms

**Status:** todo (record-only; not yet implemented)
**Depends on:** F1. **Supersedes** F1's auto-load-on-every-page-load model.

### Summary

Add a privacy-first, opt-in analytics consent model plus a Privacy Notice, Terms of Use, a persistent **Privacy settings** control, and a **Clear local game data** control — all inside the single static `sargamle.html`. No backend, framework, package, build step, new files, extra CSS framework / icon library / font. Text is plain-language and practical — **not** a claim of GDPR/DPDP/legal compliance.

### Motivation

The site uses GA4 (F1) for basic usage analytics only — no accounts, payments, ads, server DB, profiles, or user content. Give visitors genuine, easy, non-dark-pattern control over analytics while keeping the whole game fully playable without it.

### Behaviour

#### Supersedes F1 auto-load

- Do **not** load `gtag.js` before the visitor accepts.
- No page views, events, cookieless pings, or consent-denied pings before acceptance.
- No GA cookies before acceptance.
- Reject → game still fully works; visitor stays untracked until they change their choice.
- Returning **accepted** visitors may auto-load analytics; returning **rejected** visitors stay untracked.

#### Configuration object (near top of JS; single source of truth)

```javascript
const PRIVACY_CONFIG = {
  gaMeasurementId: 'G-XXXXXXXXXX',
  siteOperator: '[YOUR NAME OR LEGAL ENTITY]',
  privacyEmail: '[YOUR CONTACT EMAIL]',
  effectiveDate: '[DD MONTH YYYY]',
  governingLaw: '[STATE AND COUNTRY]',
  sourceCodeLicense: '[LICENSE NAME OR ALL RIGHTS RESERVED]',
  consentVersion: '1.0',
  consentMaxAgeDays: 180
};
```
Don't repeat these values throughout the HTML — reference the object.

#### Consent storage

Versioned localStorage key `sargamle_privacy_consent`, value:
```javascript
{ status: 'granted' | 'denied', version: '1.0', timestamp: 1784556000000 }
```
Treat as **expired / re-ask** when: older than `consentMaxAgeDays`; `version` ≠ `PRIVACY_CONFIG.consentVersion`; or missing/malformed/invalid. Re-asking must not block the game. Store no fingerprints, IPs, generated IDs, or hidden tracking values.

#### Google Consent Mode defaults (before any tag load; must NOT itself load GA or send a request)

```javascript
window.dataLayer = window.dataLayer || [];
function gtag() { window.dataLayer.push(arguments); }
gtag('consent', 'default', {
  analytics_storage: 'denied', ad_storage: 'denied',
  ad_user_data: 'denied', ad_personalization: 'denied', wait_for_update: 500
});
```

#### Consent banner (shown only when no valid choice exists)

Suggested copy: *"Sargamle uses optional analytics to understand how many people play and which game features are useful. Analytics is off unless you accept. The game works either way."*
Controls: **Accept analytics**, **Reject analytics**, **Privacy notice**.
Rules: Accept & Reject equal prominence; no preselected accept; no countdowns / repeat pop-ups / dark patterns; never blocks play; mobile+desktop; keyboard accessible; visible focus; ARIA labels; **Escape ≠ acceptance**; rejecting as easy as accepting; **not shown** on localhost / 127.0.0.1 / file://.

#### Accepting

1. Save granted. 2. `gtag('consent','update',{analytics_storage:'granted', ad_storage:'denied', ad_user_data:'denied', ad_personalization:'denied'})`. 3. Dynamically load official `gtag.js` **exactly once**. 4. After load begins: `gtag('js', new Date())` then
```javascript
gtag('config', PRIVACY_CONFIG.gaMeasurementId, {
  send_page_view: true, allow_google_signals: false, allow_ad_personalization_signals: false
});
```
5. Enable F1 Sargamle events. 6. Hide banner. Guard against duplicate script tags / `config` calls / page views. No Google Ads, remarketing, audiences, or cross-domain tracking.

#### Rejecting

Save denied; keep all consent categories denied; don't load `gtag.js`; no page view; no events; hide banner; game fully available. The F1 analytics helper must silently return when consent isn't granted.

#### Changing / withdrawing consent — persistent footer link **Privacy settings** → small dialog showing current choice

Dialog offers **Allow analytics**, **Disable analytics**, **Cancel**. On disable-after-enable:
1. Save denied. 2. `window['ga-disable-'+PRIVACY_CONFIG.gaMeasurementId] = true;` 3. Send consent update (all denied). 4. Delete JS-accessible first-party GA cookies: `_ga` and any `_ga_*`. 5. Prevent all later Sargamle analytics events. 6. Reload page if needed to fully stop tracking.
Notice must explain: withdrawing stops **future** collection but doesn't auto-erase previously aggregated data. **Do not** delete gameplay progress, preferences, or accessibility settings on withdrawal.

#### Local-storage disclosure

Notice lists that the browser may store essential local data: daily progress, previous guesses/completion state, selected raga, audio/UI prefs, practice state, consent choice — clearly distinguished from GA. State essential data stays on-device unless existing code transmits it. **Do not** claim "no data ever leaves the device" (accepted analytics go to Google; GitHub Pages serves the site).

#### Footer (small, non-distracting, mobile-usable; link-styled buttons where needed)

**Privacy**, **Terms**, **Privacy settings**, **Source code** (only if a repo URL is available/derivable — see Open questions), and a short line e.g. *"Made as an independent ear-training experiment."*

#### Privacy Notice & Terms — accessible modal/dialog in the same file

Native `<dialog>` where practical with a reasonable fallback. Support direct hash links `#privacy` and `#terms` that auto-open the matching document. Closing restores focus to the opener; browser Back behaves sensibly when a hash-opened doc is closed.

**Privacy Notice headings (plain language):** Privacy Notice (with effective date) · Who operates Sargamle (`siteOperator` + `privacyEmail`; invent no company/address/entity) · Information collected without optional analytics (no account/name/phone/email/payment; local functional state; GitHub Pages processes ordinary technical/log info under its own policy — no GitHub retention promises) · Optional Google Analytics (disabled until accepted; categories: page views, game starts, completions, win/loss, attempts, replay counts, share usage, daily-vs-practice, selected raga, approximate region, browser/device/OS, session info, pseudonymous browser ID via GA cookies; **never sent:** hidden melody, guesses, names, emails, phones, precise location, user messages, custom user IDs) · Analytics cookies (`_ga` distinguishes pseudonymous visitors; `_ga_<id>` session state; Google default up to two years but browser/actions can shorten/remove — don't claim always exactly two years) · Why analytics is used (daily usage, start/complete, usability, mode/raga usage, improvement — **no** advertising/profiling/personalised ads/data sale) · Choice and consent (optional; rejecting doesn't affect play; changeable via Privacy settings; clearing storage may re-ask) · Third-party services (Google Analytics, GitHub Pages; roles only, no control over their practices; official links `target="_blank" rel="noopener noreferrer"`) · Data retention (local data until cleared; GA retention per property config; **intended** GA4 user/event retention 14 months; aggregated reports may differ — don't guarantee deletion at exactly 14 months) · International processing (Google/GitHub may process outside visitor's country under their terms/safeguards) · Children (restrained wording per spec; **no** age gate / DOB) · Visitor choices and requests (reject/withdraw; **Clear local game data** control; browser cookie clearing; contact via email; pseudonymous records may not be linkable to a person) · Changes to this notice (may change; update effective date + consent version on material change) · Contact (operator + email; `mailto:` **only** after placeholder replaced with a valid address — no broken mailto for the placeholder).

**Terms of Use headings:** Terms of Use (effective date) · About Sargamle (free browser ear-training game using sargam concepts) · Educational & entertainment purpose (not a substitute for a qualified teacher; simplified raga modes may omit phrases/ornaments/intonation/tradition; descriptions & generated tunes may contain simplifications/mistakes) · No affiliation (independent; not affiliated with/endorsed by Wordle, NYT, Google, GitHub, or any music school/gharana/institution — named only to clarify non-affiliation) · Acceptable use (normal personal/educational use; must not disrupt the site, run harmful automated requests, impersonate the operator, or use it unlawfully; no over-restrictive clauses against ordinary inspection/learning/sharing of a public static site) · Intellectual property & source code (`sourceCodeLicense`; don't invent owner/licence; if repo has a licence, summarise + link; if none, visible placeholder needing owner review; third-party names/trademarks belong to owners) · Availability & changes (may change/error/go offline; features/ragas/daily/analytics may change or be removed; no guarantee saved progress stays compatible) · Disclaimer ("as available" to the extent permitted; don't waive non-waivable rights) · Limitation of liability (modest hobby-project language; no aggressive exclusions; to the extent permitted, operator not responsible for indirect loss from reliance/inability to access) · External services & links (third parties have own terms/privacy) · Governing law (`governingLaw` only; invent no court/city; visible placeholder warning if unreplaced) · Changes to the terms (effective date updated on material change) · Contact (operator + email).

#### Clear local game data (inside Privacy settings)

Separate control **Clear local game data**. Confirm first (explains it removes progress + preferences from this browser). Clear **only** Sargamle-owned keys via an explicit allow-list — **never** `localStorage.clear()`. Let visitor choose whether the consent decision is also cleared. Restore game to a safe fresh state after.

#### Accessibility (all consent/privacy/terms UI)

Keyboard operable; visible focus; semantic headings; sufficient contrast; readable line length; background focus trapped while modal open (where supported); focus restored on close; not colour-only; respects `prefers-reduced-motion`; usable at 200% zoom. Prefer native `<dialog>` with fallback.

#### Styling

Match existing Sargamle design; friendly/lightweight/mobile-first; consistent typography & spacing; not a corporate cookie-manager look; no extra CSS framework/icon library/font.

#### Dev/debug

No analytics on localhost / 127.0.0.1 / file://. Test hooks: `localStorage.setItem('sargamle_force_consent_banner','true')` to force the banner; `localStorage.removeItem('sargamle_privacy_consent')` to reset consent. Debug flags must not affect production visitors unless they set them locally.

### Acceptance / Verification

1. First-time visitor sees the banner. 2. Can play immediately without answering. 3. No GA request before acceptance. 4. No `_ga` cookie before acceptance. 5. Accept loads `gtag.js` exactly once. 6. Accept sends one page view. 7. Accepted visitors trigger F1 events. 8. Reject sends no page view/events. 9. Reject doesn't affect play/audio/sharing/progress. 10. Reload after accept remembers granted. 11. Reload after reject remembers denied. 12. Expired/version-mismatched decision re-shows banner. 13. Privacy settings shows current choice accurately. 14. Withdraw prevents future events. 15. Withdraw removes accessible `_ga`/`_ga_*` cookies. 16. Withdraw doesn't delete progress. 17. Clear local data removes only Sargamle keys. 18. `#privacy` opens Privacy Notice. 19. `#terms` opens Terms. 20. Back + modal close behave sensibly. 21. All controls keyboard-operable. 22. Analytics never receives hidden tune/guesses. 23. Google Signals & ad personalisation stay disabled. 24. Analytics disabled in local dev. 25. Missing config placeholders → console warning without breaking gameplay.

### Deliverables for the implementing session

Concise implementation summary · every placeholder to replace · localStorage keys used · how to test Accept/Reject/Withdraw · how to confirm in devtools GA4 isn't loaded before consent · how to force the banner in dev · storage keys found in audit · confirmation hidden melody & guesses never sent · any text a lawyer should review before launch · reminder to set GA4 retention to 14 months and keep Google Signals / ad personalisation / Google Ads linking disabled.

### Storage-key audit (done — current file)

Real gameplay keys today: **`sg-raga`** (selected raga index) and **`sg-day`** (daily progress: `{day, raga, guesses, done}`). No `sessionStorage` usage. F1 will add `disable_sargamle_analytics`, `sargamle_analytics_debug`. F2 adds `sargamle_privacy_consent` and dev-only `sargamle_force_consent_banner`. The Sargamle-owned allow-list for **Clear local game data** should therefore cover: `sg-raga`, `sg-day` (game data) and optionally `sargamle_privacy_consent` (consent — user-selectable), and dev flags. **Note:** these key names predate the `sargamle_*` convention — keep them as-is to preserve the existing local-storage format (F1/F2 must not change it).

### Open questions

- **Source-code link / repo URL.** No `github.com/...` literal exists in `sargamle.html` and there is **no LICENSE file** in the repo root. The repo is confidently derivable from the OG URLs (`https://kmcodes.github.io/AIFun/...`) → `https://github.com/kmcodes/AIFun`. Decision needed at implementation: include the **Source code** footer link to that repo (recommended, it's public), and set `sourceCodeLicense` — currently there is no licence, so it defaults to a visible "All rights reserved / owner review" placeholder unless the owner adds a LICENSE.
- **Placeholders requiring the owner before public launch:** `siteOperator`, `privacyEmail`, `effectiveDate`, `governingLaw`, `sourceCodeLicense`, and the real `gaMeasurementId` (shared with F1). `mailto:` must stay non-linked until `privacyEmail` is a valid address.
- **Legal review.** Privacy Notice + Terms are plain-language, not a compliance guarantee; flag for owner/lawyer review before public launch (esp. governing law, liability, retention wording).
