# Harvesta phone voice chat

## Why the current phone link cannot use live voice reliably

The Wi-Fi address shown in the phone screenshot starts with `http://10...` and
the browser marks it as insecure. Browser microphone access is designed for a
trusted HTTPS page (or `localhost`). A private network address is not
`localhost` on the phone.

Harvesta now checks this before opening the microphone and gives a specific
message instead of repeatedly showing “Preparing a local answer”. It also
distinguishes denied permission, missing microphone, no speech, unsupported
language, and browser speech-service network errors.

## What works immediately on the current HTTP test link

1. Tap the Harvesta message box.
2. Tap the microphone on the phone keyboard.
3. Speak the question.
4. Check the text and tap Harvesta’s Send arrow.

This is keyboard dictation. The phone keyboard owns microphone permission, so
it can work even though the web page itself is not trusted for microphone use.

## What is required for the Harvesta live-voice button

Use one of these trusted options:

1. Deploy the frontend and backend behind a real HTTPS domain. This is the
   recommended option for real users and Play Store preparation.
2. For private development, create a certificate for the current LAN hostname
   or IP, trust its certificate authority on the phone, and set both
   `HARVESTA_HTTPS_CERT` and `HARVESTA_HTTPS_KEY` in `frontend/.env` before
   restarting the frontend.

Do not bypass a certificate warning. A self-signed server certificate that the
phone does not trust is not a reliable secure context. The API now uses the
same origin through the development proxy, so an HTTPS frontend will not be
blocked by an HTTP API as mixed content.

## Phone permission check after HTTPS is ready

In Chrome on Android: open the site, tap the address-bar site controls, open
Permissions, set Microphone to Allow, reload Harvesta, and then tap its mic.
The exact labels can vary by Android and Chrome version.

Browser speech recognition and Harvesta’s local AI are separate. Chrome may
use its own online speech-recognition service, so the phone can still need an
internet connection to turn speech into text even when Harvesta’s answer model
runs locally on the computer.

## Chat speed behavior

- A first chat turn now uses one request and one database commit.
- Common farm questions, including crop-status questions and the common
  “crip status” typo, use instant built-in agricultural guidance.
- A detailed local model gets six seconds. If it is not ready, Harvesta returns
  clearly labelled built-in guidance rather than spinning for 30–90 seconds.
- The built-in response never claims that saved records are live sensor data.
- Browser requests stop with a useful connection message instead of spinning
  forever.
