DROP TABLE IF EXISTS courses;

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    trimester INTEGER NOT NULL,
    code TEXT NOT NULL,
    content TEXT NOT NULL
);
DROP TABLE IF EXISTS templates;
    CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    field_name TEXT NOT NULL,
    field_order INTEGER NOT NULL
);


drop table if exists users;
    create table users (
    id integer primary key autoincrement,
    username text not null,
    password text not null
);

DROP TABLE IF EXISTS posts;