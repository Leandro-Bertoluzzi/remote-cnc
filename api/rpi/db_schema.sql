-- Adminer 4.8.1 PostgreSQL 16.1 dump

\connect "cnc_db";

DROP TABLE IF EXISTS "files";
DROP SEQUENCE IF EXISTS files_id_seq;
CREATE SEQUENCE files_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."files" (
    "id" integer DEFAULT nextval('files_id_seq') NOT NULL,
    "user_id" integer,
    "file_name" character varying(150) NOT NULL,
    "created_at" timestamp DEFAULT now() NOT NULL,
    "file_hash" character varying(150),
    CONSTRAINT "files_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


DROP TABLE IF EXISTS "materials";
DROP SEQUENCE IF EXISTS materials_id_seq;
CREATE SEQUENCE materials_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."materials" (
    "id" integer DEFAULT nextval('materials_id_seq') NOT NULL,
    "name" character varying(50) NOT NULL,
    "description" character varying(150) NOT NULL,
    "added_at" timestamp DEFAULT now() NOT NULL,
    CONSTRAINT "materials_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


DROP TABLE IF EXISTS "tasks";
DROP SEQUENCE IF EXISTS tasks_id_seq;
CREATE SEQUENCE tasks_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TYPE task_status AS ENUM
    (
        'pending_approval',
        'on_hold',
        'in_progress',
        'finished',
        'rejected',
        'cancelled'
    );

CREATE TABLE "public"."tasks" (
    "id" integer DEFAULT nextval('tasks_id_seq') NOT NULL,
    "created_at" timestamp NOT NULL,
    "status_updated_at" timestamp,
    "priority" integer NOT NULL,
    "status" task_status NOT NULL,
    "user_id" integer NOT NULL,
    "file_id" integer NOT NULL,
    "name" character varying(50) NOT NULL,
    "note" character varying(150),
    "tool_id" integer NOT NULL,
    "material_id" integer NOT NULL,
    "admin_id" integer,
    "cancellation_reason" character varying(150),
    CONSTRAINT "tasks_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


DROP TABLE IF EXISTS "tools";
DROP SEQUENCE IF EXISTS tools_id_seq;
CREATE SEQUENCE tools_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TABLE "public"."tools" (
    "id" integer DEFAULT nextval('tools_id_seq') NOT NULL,
    "name" character varying(50) NOT NULL,
    "description" character varying(150) NOT NULL,
    "added_at" timestamp DEFAULT now() NOT NULL,
    CONSTRAINT "tools_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


DROP TABLE IF EXISTS "users";
DROP SEQUENCE IF EXISTS users_id_seq;
CREATE SEQUENCE users_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1;

CREATE TYPE role AS ENUM
    ('user', 'admin');

CREATE TABLE "public"."users" (
    "id" integer DEFAULT nextval('users_id_seq') NOT NULL,
    "name" character varying(50) NOT NULL,
    "email" character varying(50) NOT NULL,
    "password" character varying(150) NOT NULL,
    "role" role NOT NULL,
    CONSTRAINT "unique_users_email" UNIQUE ("email"),
    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


ALTER TABLE ONLY "public"."files" ADD CONSTRAINT "fk_user_id" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT DEFERRABLE;

ALTER TABLE ONLY "public"."tasks" ADD CONSTRAINT "fk_admin_id" FOREIGN KEY (admin_id) REFERENCES users(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."tasks" ADD CONSTRAINT "fk_file_id" FOREIGN KEY (file_id) REFERENCES files(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."tasks" ADD CONSTRAINT "fk_material_id" FOREIGN KEY (material_id) REFERENCES materials(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."tasks" ADD CONSTRAINT "fk_owner_id" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE NOT DEFERRABLE;
ALTER TABLE ONLY "public"."tasks" ADD CONSTRAINT "fk_tool_id" FOREIGN KEY (tool_id) REFERENCES tools(id) NOT DEFERRABLE;

-- 2024-02-06 19:43:29.544543+00
