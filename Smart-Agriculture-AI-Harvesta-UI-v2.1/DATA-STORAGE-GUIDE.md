# Where Harvesta stores your data

Verified on 4 September 2026 using read-only queries. No production records were changed for this check.

## Your active database

Harvesta is connected to **Supabase PostgreSQL**, in your existing smart_agriculture project. It is not currently using the local SQLite fallback.

Open [your Supabase project](https://supabase.com/dashboard/project/dsddhvodoixlzzqjzvny), choose **Table Editor**, select the **public** schema, and open a table below.

Do not share the database connection password, service keys, access tokens, or screenshots of private records.

| Information | Database table(s) | What is saved |
| --- | --- | --- |
| Accounts | users | Account identity, verification state, role and password hashes—not readable passwords |
| Profile | farmer_profiles | Phone, address, district, state, country, bio, crop, experience and profile colour |
| App settings | app_preferences | Saved language, theme, layout and voice preferences |
| Farms and crops | farms, crops | Farm details, crop dates, stages and health information |
| Field analyses | field_analysis_history | Entered soil measurements, weather values and saved recommendations |
| Weather snapshots | weather_snapshots | Separate saved weather snapshots when that workflow records them |
| Inventory | inventory_items | Saved farm supplies, tools, equipment, quantities and stock thresholds |
| Login sessions | user_sessions | Login/logout times, last activity, session duration fields, device information and a hashed IP |
| Selected app actions | activity_events | Instrumented actions such as dashboard views, profile/settings saves and other supported feature events |
| Audit history | audit_logs | Supported administrative, account and security-related actions |
| Notifications | notifications, notification_preferences | Notifications and the user's delivery preferences |
| AI conversations | ai_chat_conversations, ai_chat_messages | Conversation records, sent messages and saved AI replies |
| Disease screening | crop_disease_scans | Screening results and a reference to the uploaded image |
| Sensors | sensor_devices, sensor_readings | Registered gateways and timestamped measurements received from them |

Each farmer's records are associated with their account. Application endpoints restrict ordinary farmers to their own records. The Supabase project owner's dashboard permissions are separate from Harvesta's Farmer/Admin role; changing profile colour does not change that role.

## What was present during this check

- 2 accounts, 1 saved profile and 1 saved app-preference record.
- 2 field analyses.
- 11 login-session records, 219 activity events and 9 audit events.
- 6 AI conversations and 14 messages.
- 17 notifications and 2 notification-preference records.
- No saved farms, crops, inventory items, disease scans, sensor gateways, sensor readings or separate weather snapshots yet.

These are point-in-time counts and will change as you use the app. An empty table means the relevant data has not been saved yet; it is not evidence that Supabase is disconnected. Weather can exist inside a field-analysis record even while weather_snapshots is empty.

## Photos and downloads are different

**Supabase Storage for photos is not currently enabled.** Scan image files are configured to be stored on this laptop, under:

`data/uploads/disease_scans`

The full directory is inside the nested Smart-Agriculture-AI-Harvesta-UI-v2.1 project. The database stores the image reference and scan result. There were no saved scan records when checked.

Do not delete that folder if you later upload photos. Moving photos to Supabase Storage requires a separate configuration and migration step; the database connection alone does not upload them.

PDF and CSV reports are generated from saved records when requested and downloaded by your browser. They are not automatically kept as PDF files in Supabase. The five report categories do not mean five pre-existing report files.

## What is temporary or browser-only?

- Unsaved form edits stay in memory and are discarded if you leave or reload without saving.
- The current GPS display is temporary; it is not continuous location tracking.
- A local preference cache and login/session identifiers are kept in browser storage. Saved app preferences also have their database record.
- Raw microphone recordings are not stored by the app's current voice-chat code. Recognized text that you send is saved as a chat message.
- Not every click or second of use is recorded. The app logs selected actions and periodic session activity; session duration is not a precise measurement of focused work.

## How Save changes now works

1. Select a colour, theme, language or other editable value.
2. It stays as an unsaved draft. The active setting and large profile avatar remain unchanged.
3. Press **Save changes**.
4. After the server confirms the save, the app applies the returned values.
5. A saved profile colour is used by the profile, sidebar avatar and dashboard avatar, and is loaded again after login or refresh.
6. If saving fails, an error is shown and the previous saved values remain active. You can retry or discard the draft.
