-- Rode isso no Supabase: painel do projeto > SQL Editor > New query

create table if not exists base_dados (
    id bigint generated always as identity primary key,
    ano integer not null,
    mes integer not null,
    cidade_agrupada text not null,
    class_segmentos text not null,
    abertura_empresas integer not null
);

create index if not exists idx_base_dados_ano_mes on base_dados (ano, mes);
create index if not exists idx_base_dados_cidade on base_dados (cidade_agrupada);
create index if not exists idx_base_dados_segmento on base_dados (class_segmentos);

-- Row Level Security: como o agente acessa via SUPABASE_SECRET_KEY
-- (service_role), o RLS abaixo é opcional — ele só passa a valer se
-- algum dia você expuser essa tabela também via SUPABASE_PUBLISHABLE_KEY
-- (ex.: um dashboard público). Deixe habilitado por segurança:
alter table base_dados enable row level security;

create policy "Leitura pública dos dados agregados"
    on base_dados for select
    using (true);
-- Não criamos policy de insert/update/delete: só o service_role
-- (que ignora RLS) pode escrever — ou seja, só o seu backend.
