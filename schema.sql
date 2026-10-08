create table users (
    id bigserial PRIMARY KEY, 
    phone text unique not null, 
    name text not null,
    password_hash text not null, 
    created_at timestamptz not null default now()
);

create table accounts (
    id bigserial primary key, 
    user_id bigint not null references users(id), 
    balance bigint not null default 0 check (balance>=0), 
    status text not null default 'active' check (status in ('active','blocked')), 
    created_at timestamptz not null default now()
);

create table transactions (
    id bigserial primary key, 
    orig_id bigint references accounts(id), 
    dest_id bigint references accounts(id), 
    type text not null check (type in ('transfer','payment','withdrawal','deposit','refund','fee')), 
    amount bigint not null check (amount>0), 
    description text not null, 
    created_at timestamptz not null default now(),
    constraint has_account check (orig_id is not null or dest_id is not null)
);

create table messages (
    id bigserial primary key, 
    conversation_id bigint references conversations(id) not null, 
    role text check (role in ('model','user')),
    content text not null, 
    created_at timestamptz not null default now()
);

create table conversations (
    id bigserial primary key, 
    user_id bigint references users(id) not null,
    last_interaction_id text
);