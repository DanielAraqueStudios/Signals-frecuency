# mobile-app

Expo + React Native + TypeScript app for the parts-sorting platform. A
worker logs in (or registers), captures a photo of a part, uploads it for
classification, and can review past results. No actuator/sorting UI — this
is identification/logging only.

## Screens

- **Login / Register** — hit `auth-service` (via its documented
  `/register`, `/login`, `/refresh` endpoints), store tokens on success.
- **Capture** — take a photo (or pick one from the library), upload it to
  the API Gateway, show the returned label/confidence with a distinct
  **PREVIEW / NOT A REAL MODEL YET** badge whenever the response says
  `stub: true` (classification-service has no trained model yet — see its
  README). A result is never shown as if it were real when it isn't.
- **History** — past capture results for the logged-in user, pull-to-refresh,
  same stub-vs-real badge per row.

## Setup

```bash
npm install
# or: npx expo install   (resolves versions against the installed Expo SDK)
npx expo start
```

Scan the QR code with Expo Go (iOS/Android), or press `a`/`i` for an
emulator/simulator, or `w` for web.

## Environment variables

| Variable | Purpose | Default (placeholder) |
|---|---|---|
| `API_GATEWAY_URL` | Base URL of `api-gateway` — image upload/history | `http://localhost:8000` |
| `AUTH_URL` | Base URL of `auth-service` — register/login/refresh | `http://localhost:8001` |

Set them before `expo start`, e.g.:

```bash
API_GATEWAY_URL=https://api-gateway.example.up.railway.app \
AUTH_URL=https://auth-service.example.up.railway.app \
npx expo start
```

`app.config.ts` reads `process.env.API_GATEWAY_URL` / `process.env.AUTH_URL`
at config-evaluation time and puts them under Expo's `extra`; the app reads
them back at runtime via `expo-constants` in `src/api/config.ts`. If unset,
both fall back to the `localhost` placeholders above — those will not work
against a deployed backend, so treat them as a loud reminder to configure
the app, not a working default.

## API contracts this app is built against

These two contracts are fixed and documented, but **not yet implemented**
server-side as of this app being written — `api-gateway`'s `/images`
endpoints are being built in parallel. Coded against the documented shape;
nothing here should need to change once that lands unless the contract
itself changes.

- `POST {API_GATEWAY_URL}/images` — multipart form, one file field named
  `image`, `Authorization: Bearer <accessToken>`. Response:
  `{"label": string, "confidence": number | null, "stub": boolean, "reason"?: string}`.
- `GET {API_GATEWAY_URL}/images` — same auth, returns
  `[{id, label, confidence, stub, createdAt}, ...]`.

`auth-service`'s contract (already built and tested — see
`services/auth-service/README.md`) is consumed as-is: `POST /register`
returns the created user (no token — the app logs in right after),
`POST /login` and `POST /refresh` return `{access_token, refresh_token}`.
Access tokens expire in 15 minutes; `src/api/client.ts` catches a 401,
calls `/refresh` once with the stored refresh token, retries the original
request once, and only then drops the user back to the Login screen.

## Design choices worth flagging

- **Camera capture uses `expo-image-picker`'s `launchCameraAsync`**, not a
  custom `expo-camera` `<CameraView>` live-preview screen. It handles the
  permission prompt and capture UI itself in one call, so there is no
  custom shutter/preview UI that could be silently wrong without a
  physical device to test on. `launchImageLibraryAsync` is offered
  alongside it as a fallback (e.g. for a simulator with no camera).
- **Tokens are stored with `expo-secure-store`**, not `AsyncStorage` —
  Keychain (iOS) / EncryptedSharedPreferences-backed Keystore (Android)
  rather than plain unencrypted disk, appropriate for auth secrets.
- **No `@react-navigation/bottom-tabs` dependency** — the logged-in
  Capture/History switch is a small local-state toggle inside one screen
  (`App.tsx`'s `LoggedInHome`) instead of a second navigation library, to
  keep the dependency list lean for this MVP. Swap in real tabs later if
  the screen count grows.

## What was actually verified in this environment

- `npm install` — ran for real, succeeded (1151 packages, some deprecation
  warnings from transitive deps, no install failures).
- `npx tsc --noEmit` — clean, no type errors, after `npm install`.
- `npx expo-doctor` — 17/17 checks passed (this caught and fixed a real
  version mismatch: `expo-image-picker` was pinned to `~15.0.7`, but the
  installed Expo SDK 51 expects `~15.1.0` — bumped in `package.json`).
- **Not verified**: actually launching `npx expo start` and exercising the
  app on a device/simulator/Expo Go — no physical device or emulator is
  available in this environment. The screens, navigation wiring, and API
  calls were checked by careful reading against React Navigation's
  native-stack API and Expo SDK 51's documented APIs
  (`expo-image-picker`, `expo-secure-store`, `expo-constants`), and by the
  clean type-check above, but a real render/interaction pass has not
  happened. `api-gateway`'s `/images` endpoints also don't exist yet (see
  above), so no live end-to-end request has been made either — do that
  once both sides are deployed together.
