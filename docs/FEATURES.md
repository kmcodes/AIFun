# Sargamle — Feature Details

Per-feature specs for planned work. To-do index: [TODO.md](TODO.md).

Template per feature: **Summary · Motivation · Behaviour · Acceptance/Verification · Open questions**.

---

## F1 — GA4 Analytics

**Status:** todo (record-only; not yet implemented)

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
