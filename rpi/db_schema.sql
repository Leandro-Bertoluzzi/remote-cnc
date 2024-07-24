BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> dda662b6775d

CREATE TABLE users (
    id SERIAL NOT NULL,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    password VARCHAR(150) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TYPE role AS ENUM ('user', 'admin');

ALTER TABLE users ADD COLUMN role role NOT NULL;

INSERT INTO alembic_version (version_num) VALUES ('dda662b6775d') RETURNING alembic_version.version_num;

-- Running upgrade dda662b6775d -> a4a5b53fb397

CREATE TABLE files (
    id SERIAL NOT NULL,
    user_id INTEGER,
    file_name VARCHAR(150) NOT NULL,
    file_path VARCHAR(150) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE files ADD CONSTRAINT fk_user_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE;

UPDATE alembic_version SET version_num='a4a5b53fb397' WHERE alembic_version.version_num = 'dda662b6775d';

-- Running upgrade a4a5b53fb397 -> b45f388692dc

CREATE TABLE tasks (
    id SERIAL NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    status_updated_at TIMESTAMP WITHOUT TIME ZONE,
    priority INTEGER NOT NULL,
    PRIMARY KEY (id)
);

CREATE TYPE task_status AS ENUM ('pending_approval', 'on_hold', 'in_progress', 'finished', 'rejected');

ALTER TABLE tasks ADD COLUMN status task_status NOT NULL;

UPDATE alembic_version SET version_num='b45f388692dc' WHERE alembic_version.version_num = 'a4a5b53fb397';

-- Running upgrade b45f388692dc -> 677cfe19a165

ALTER TABLE tasks ADD COLUMN user_id INTEGER NOT NULL;

ALTER TABLE tasks ADD COLUMN file_id INTEGER NOT NULL;

ALTER TABLE tasks ADD CONSTRAINT fk_owner_id FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE tasks ADD CONSTRAINT fk_file_id FOREIGN KEY(file_id) REFERENCES files (id);

UPDATE alembic_version SET version_num='677cfe19a165' WHERE alembic_version.version_num = 'b45f388692dc';

-- Running upgrade 677cfe19a165 -> 8475035ee19e

CREATE TABLE tools (
    id SERIAL NOT NULL,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(150) NOT NULL,
    added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

UPDATE alembic_version SET version_num='8475035ee19e' WHERE alembic_version.version_num = '677cfe19a165';

-- Running upgrade 8475035ee19e -> 47f8b3a7f591

ALTER TABLE users ADD CONSTRAINT unique_users_email UNIQUE (email);

UPDATE alembic_version SET version_num='47f8b3a7f591' WHERE alembic_version.version_num = '8475035ee19e';

-- Running upgrade 47f8b3a7f591 -> f0fe8ee5571c

CREATE TABLE materials (
    id SERIAL NOT NULL,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(150) NOT NULL,
    added_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (id)
);

UPDATE alembic_version SET version_num='f0fe8ee5571c' WHERE alembic_version.version_num = '47f8b3a7f591';

-- Running upgrade f0fe8ee5571c -> 6d8972b34033

ALTER TABLE tasks ADD COLUMN name VARCHAR(50) NOT NULL;

ALTER TABLE tasks ADD COLUMN note VARCHAR(150);

UPDATE alembic_version SET version_num='6d8972b34033' WHERE alembic_version.version_num = 'f0fe8ee5571c';

-- Running upgrade 6d8972b34033 -> 8c8c413bf8ac

ALTER TABLE tasks ADD COLUMN tool_id INTEGER NOT NULL;

ALTER TABLE tasks ADD COLUMN material_id INTEGER NOT NULL;

ALTER TABLE tasks ADD CONSTRAINT fk_tool_id FOREIGN KEY(tool_id) REFERENCES tools (id);

ALTER TABLE tasks ADD CONSTRAINT fk_material_id FOREIGN KEY(material_id) REFERENCES materials (id);

UPDATE alembic_version SET version_num='8c8c413bf8ac' WHERE alembic_version.version_num = '6d8972b34033';

-- Running upgrade 8c8c413bf8ac -> bb56f0eca8c5

ALTER TABLE tasks ADD COLUMN admin_id INTEGER;

ALTER TABLE tasks ADD CONSTRAINT fk_admin_id FOREIGN KEY(admin_id) REFERENCES users (id);

UPDATE alembic_version SET version_num='bb56f0eca8c5' WHERE alembic_version.version_num = '8c8c413bf8ac';

-- Running upgrade bb56f0eca8c5 -> ef375042cb3f

ALTER TABLE tasks ADD COLUMN cancellation_reason VARCHAR(150);

CREATE TYPE temp_task_status AS ENUM ('cancelled', 'pending_approval', 'on_hold', 'in_progress', 'finished', 'rejected');

ALTER TABLE tasks ALTER COLUMN status TYPE temp_task_status USING status::text::temp_task_status;

DROP TYPE task_status;

CREATE TYPE task_status AS ENUM ('cancelled', 'pending_approval', 'on_hold', 'in_progress', 'finished', 'rejected');

ALTER TABLE tasks ALTER COLUMN status TYPE task_status USING status::text::task_status;

DROP TYPE temp_task_status;

UPDATE alembic_version SET version_num='ef375042cb3f' WHERE alembic_version.version_num = 'bb56f0eca8c5';

-- Running upgrade ef375042cb3f -> c5cba49f95bf

ALTER TABLE files DROP COLUMN file_path;

ALTER TABLE files ADD COLUMN file_hash VARCHAR(150);

UPDATE alembic_version SET version_num='c5cba49f95bf' WHERE alembic_version.version_num = 'ef375042cb3f';

-- Running upgrade c5cba49f95bf -> 3235826a58f1

CREATE TYPE temp_task_status AS ENUM ('failed', 'pending_approval', 'on_hold', 'in_progress', 'finished', 'rejected', 'cancelled');

ALTER TABLE tasks ALTER COLUMN status TYPE temp_task_status USING status::text::temp_task_status;

DROP TYPE task_status;

CREATE TYPE task_status AS ENUM ('failed', 'pending_approval', 'on_hold', 'in_progress', 'finished', 'rejected', 'cancelled');

ALTER TABLE tasks ALTER COLUMN status TYPE task_status USING status::text::task_status;

DROP TYPE temp_task_status;

UPDATE alembic_version SET version_num='3235826a58f1' WHERE alembic_version.version_num = 'c5cba49f95bf';

-- Running upgrade 3235826a58f1 -> 5269cf543947

UPDATE tasks SET status='cancelled' WHERE tasks.status = 'rejected';

CREATE TYPE temp_task_status AS ENUM ('pending_approval', 'on_hold', 'in_progress', 'finished', 'cancelled', 'failed');

ALTER TABLE tasks ALTER COLUMN status TYPE temp_task_status USING status::text::temp_task_status;

DROP TYPE task_status;

CREATE TYPE task_status AS ENUM ('pending_approval', 'on_hold', 'in_progress', 'finished', 'cancelled', 'failed');

ALTER TABLE tasks ALTER COLUMN status TYPE task_status USING status::text::task_status;

DROP TYPE temp_task_status;

UPDATE alembic_version SET version_num='5269cf543947' WHERE alembic_version.version_num = '3235826a58f1';

COMMIT;

