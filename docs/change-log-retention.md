# ChangeLog data and retention policy

ChangeLog is the application's synchronization feed. It is not a permanent audit archive.

New user registration events contain the entity type, entity ID, operation, version, actor IDs, and timestamp. They do not copy the user's email, display name, or authentication provider into the event payload. Clients can retrieve the current profile from `/users/me`.

ChangeLog entries are retained for 365 days. The `make db-prune-change-log` command deletes expired rows and records the highest expired sequence for each account. Docker Compose runs this command daily through the `change-log-pruner` service. Other deployment environments must schedule the command daily.

If a client requests changes from a sequence older than the retained history, the API returns HTTP 410 with `data.resync_required` set to `true` and a `data.restart_sequence`. The client must fetch a complete current snapshot from the resource list endpoints, then resume change polling after `restart_sequence`. The client must save the restart sequence only after the snapshot succeeds.

An account deletion flow must remove the account's ChangeLog and sync state in the same transaction as the account data deletion. The current schema has required foreign keys from ChangeLog to both the account owner and the event actor, so account deletion must process ChangeLog before deleting the user.

User IDs in ChangeLog are still linkable personal data. Any future retention period or account deletion flow must account for those identifiers as well as event payloads.

Existing user registration events may still contain email, display name, and authentication provider in their payload. They remain subject to the 365-day retention period. No backfill migration rewrites existing rows.

PostgreSQL does not support removing enum labels with a simple `ALTER TYPE`. The downgrade for revision `91e2a3b4c5d6` therefore retains the added `entity_type` labels. It refuses to proceed if rows in ChangeLog, sync state, relations, or monitoring events still use those labels, so the prior application version will not encounter enum values it cannot decode.
