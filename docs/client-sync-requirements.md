# Client synchronization requirements

This document defines the client behavior for the ChangeLog API. A client stores its ChangeLog cursor with the local account and client device state.

## Normal incremental sync

1. Request `GET /change-logs?after_sequence=<cursor>&limit=100`.
2. Apply returned entries in ascending `sequence` order. Treat applying an entry as idempotent by using its entity ID and version; process `delete` as a local removal.
3. Persist the new cursor only after all entries in the response have been applied durably. Set it to the last applied sequence. If the response is empty, retain the existing cursor.
4. Continue requesting pages while a response contains 100 entries.

Do not advance the cursor when local application fails. Retry the same request after recovering local state.

## Recovery after HTTP 410

When the API returns `410 Gone` with `data.resync_required: true` and `data.restart_sequence`:

1. Keep the old cursor until recovery completes. Start a replacement local snapshot rather than applying incremental events from the expired cursor.
2. Fetch the current profile with `GET /users/me`; fetch projects with `GET /projects`; fetch devices with `GET /devices`; fetch groups with `GET /device-groups`; and fetch connections, services, containers, and databases from their user collection endpoints. For each project, fetch its environments and project-device links. Follow any additional collection endpoint needed for data the client stores.
3. Build the replacement snapshot without exposing a partially refreshed cache. Store it atomically, or stage it and swap it into use only after every required request succeeds.
4. After the snapshot has been stored successfully, persist `restart_sequence` as the new cursor.
5. Resume normal incremental sync with `GET /change-logs?after_sequence=<restart_sequence>`. Changes made while the snapshot was loading have larger sequence values and will be returned for application.

If any snapshot request or local snapshot commit fails, discard the incomplete snapshot and keep the previous cursor. Retry the recovery flow; do not store `restart_sequence` early.

The currently exposed collection endpoints cover user profile, projects, devices, device groups, connections, services, containers, and databases. Project environments and project-device links are listed under their project routes. The client must include every resource collection it persists in its snapshot. New synchronizable resource types require both a user-scoped snapshot collection and an entry in this protocol before clients depend on them.

## Backend and integration guarantees

- ChangeLog pages are scoped to the authenticated user, ordered by sequence, and limited to 100 entries per request.
- A 410 response provides a restart sequence at least as high as the user's latest retained sequence at the time the expired cursor is checked.
- The integration workflow covers expired-cursor detection, fetching the current snapshot, a change occurring during that fetch, and polling after the restart sequence.
