# NoorAI Database Schema

## users
| Column | Type | Constraints | Purpose |
|---|---|---|---|
| id | UUID | PK, default gen | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login identifier |
| hashed_password | VARCHAR(255) | NOT NULL | bcrypt password hash |
| first_name | VARCHAR(100) | NOT NULL | Display name |
| last_name | VARCHAR(100) | NOT NULL | Display name |
| location_city | VARCHAR(100) | NULLABLE | For prayer times (e.g. "Singapore") |
| location_lat | FLOAT | NULLABLE | For prayer time calculation |
| location_lng | FLOAT | NULLABLE | For prayer time calculation |
| madhab | VARCHAR(20) | DEFAULT 'shafii' | Affects prayer time calc & fiqh answers |
| created_at | TIMESTAMP | DEFAULT now() | Account creation date |
| updated_at | TIMESTAMP | DEFAULT now() | Last profile update |
| currency | VARCHAR(3) | DEFAULT 'USD' | ISO currency code used for zakat calculations and display |

## prayer_logs
| Column | Type | Constraints | Purpose |
|---|---|---|---|
| id | UUID | PK, default gen | Unique log entry |
| user_id | UUID | FK -> users.id, NOT NULL | Whose prayer this is |
| prayer_date | DATE | NOT NULL | Which calendar day |
| prayer_name | VARCHAR(20) | NOT NULL | fajr / dhuhr / asr / maghrib / isha |
| completed | BOOLEAN | DEFAULT false | Was it prayed? |
| completed_at | TIMESTAMP | NULLABLE | Exact time marked done |
| created_at | TIMESTAMP | DEFAULT now() | Row creation time |

Unique constraint on (user_id, prayer_date, prayer_name) - one row per prayer per day per user.

## zakat_records
| Column | Type | Constraints | Purpose |
|---|---|---|---|
| id | UUID | PK, default gen | Unique calculation |
| user_id | UUID | FK -> users.id, NOT NULL | Whose calculation |
| cash_amount | NUMERIC(12,2) | DEFAULT 0 | Cash & savings entered |
| gold_grams | NUMERIC(10,2) | DEFAULT 0 | Gold weight entered |
| silver_grams | NUMERIC(10,2) | DEFAULT 0 | Silver weight entered |
| investments_amount | NUMERIC(12,2) | DEFAULT 0 | Stocks/investments entered |
| business_assets_amount | NUMERIC(12,2) | DEFAULT 0 | Business assets entered |
| total_wealth | NUMERIC(12,2) | NOT NULL | Sum of all above (computed) |
| nisab_threshold | NUMERIC(12,2) | NOT NULL | Nisab at time of calc |
| zakat_due | NUMERIC(12,2) | NOT NULL | Final amount owed |
| calculated_at | TIMESTAMP | DEFAULT now() | When this calc was run |

## chat_sessions
| Column | Type | Constraints | Purpose |
|---|---|---|---|
| id | UUID | PK, default gen | One conversation thread |
| user_id | UUID | FK -> users.id, NOT NULL | Owner of the chat |
| title | VARCHAR(255) | NULLABLE | Auto-generated chat title (e.g. "Surah Al-Fatiha") |
| created_at | TIMESTAMP | DEFAULT now() | Chat start time |
| updated_at | TIMESTAMP | DEFAULT now() | Last message time |

## chat_messages
| Column | Type | Constraints | Purpose |
|---|---|---|---|
| id | UUID | PK, default gen | One message |
| session_id | UUID | FK -> chat_sessions.id, NOT NULL | Which conversation |
| role | VARCHAR(10) | NOT NULL | 'user' or 'assistant' |
| content | TEXT | NOT NULL | The message text |
| sources | JSONB | NULLABLE | List of sources cited (Quran refs, web links, etc.) |
| created_at | TIMESTAMP | DEFAULT now() | Message timestamp |

## document_chunks
| Column | Type | Constraints | Purpose |
|---|---|---|---|
| id | UUID | PK, default gen | One chunk of text |
| source_title | VARCHAR(255) | NOT NULL | Which document/book it came from |
| content | TEXT | NOT NULL | The actual text chunk |
| embedding | VECTOR(384) | NOT NULL | pgvector embedding for similarity search |
| metadata | JSONB | NULLABLE | Page number, chapter, tags, etc. |
| created_at | TIMESTAMP | DEFAULT now() | When ingested |

This table has no user_id - it's shared knowledge base content, not per-user.

## How the tables connect

```
users
  |
  |-- prayer_logs    (1 user -> many prayer logs)
  |-- zakat_records  (1 user -> many zakat calculations)
  |-- chat_sessions  (1 user -> many chat sessions)
                          |
                          |-- chat_messages (1 session -> many messages)

document_chunks (standalone - searched via vector similarity,
                  not linked to users directly)
```