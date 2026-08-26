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


create or replace function totais_aberturas(
    p_ano integer default null,
    p_mes integer default null,
    p_cidade text default null,
    p_segmento text default null,
    p_agrupar_por text default 'ano'  -- 'ano' | 'mes' | 'cidade' | 'segmento'
)
returns table(chave text, total bigint)
language sql
stable
as $$
    select
        case p_agrupar_por
            when 'ano' then ano::text
            when 'mes' then mes::text
            when 'cidade' then cidade_agrupada
            when 'segmento' then class_segmentos
            else 'total'
        end as chave,
        sum(abertura_empresas) as total
    from base_dados
    where (p_ano is null or ano = p_ano)
      and (p_mes is null or mes = p_mes)
      and (p_cidade is null or cidade_agrupada ilike '%' || p_cidade || '%')
      and (p_segmento is null or class_segmentos ilike '%' || p_segmento || '%')
    group by chave
    order by chave;
$$;


alter table base_dados enable row level security;

create policy "Leitura pública dos dados agregados"
    on base_dados for select
    using (true);
-- Não criamos policy de insert/update/delete: só o service_role
-- (que ignora RLS) pode escrever — ou seja, só o seu backend.
