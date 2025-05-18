drop table if exists users;
create table users (
    id integer primary key autoincrement, username text not null unique, password text not null, user_type text not null 
);