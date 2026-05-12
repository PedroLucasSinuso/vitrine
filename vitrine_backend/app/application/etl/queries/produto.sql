SELECT  
    d.cdprincipal       as codigo_chamada,
    g.nmgrupo           as grupo,
    COALESCE(f.dsfamilia, 'SEM FAMILIA') as familia,
    d.dsdetalhe         as nome,
    d.vlprecovenda      as preco_venda,
    d.vlprecocusto      as preco_custo,
    SUM(e.qtestoque)    as estoque

FROM wshop.detalhe d
LEFT JOIN wshop.familia f   ON d.idfamilia = f.idfamilia
LEFT JOIN wshop.produto p   ON d.idproduto = p.idproduto
LEFT JOIN wshop.grupo   g   ON p.idgrupo = g.idgrupo
LEFT JOIN wshop.estoque e   ON d.iddetalhe = e.iddetalhe

WHERE e.dtreferencia = (
    SELECT MAX(e2.dtreferencia)
    FROM wshop.estoque e2
    WHERE e2.iddetalhe = d.iddetalhe
)

GROUP BY
    d.cdprincipal,
    g.nmgrupo,
    f.dsfamilia,
    d.dsdetalhe,
    d.vlprecovenda,
    d.vlprecocusto;