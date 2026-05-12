SELECT
    doc.iddocumentoitem AS id_item,
    d.iddocumento,
    d.idnfe AS id_nfe,
    d.dtemissao AS emissao,
    d.hrreferencia AS hora,
    d.tpoperacao AS operacao,
    d.idoperacao AS id_operacao,
    d.stdocumentocancelado AS cancelado,
    d.vltotal AS total_documento,
    d.tpdevolucao AS tipo_devolucao,
    g.nmgrupo AS grupo,
    f.dsfamilia AS familia,
    det.cdprincipal AS codigo,
    det.dsdetalhe AS produto,
    det.vlprecocusto AS custo,
    det.vlprecovenda AS venda,
    doc.qtitem AS qtd_item,
    doc.vlmovimento AS receita_produto,
    doc.vlunitario AS valor_unitario
FROM wshop.documen d
JOIN wshop.docitem doc ON doc.iddocumento = d.iddocumento
JOIN wshop.detalhe det ON doc.iddetalhe = det.iddetalhe
JOIN wshop.produto p ON det.idproduto = p.idproduto
LEFT JOIN wshop.grupo g ON p.idgrupo = g.idgrupo
LEFT JOIN wshop.familia f ON det.idfamilia = f.idfamilia
WHERE d.dtemissao >= :data_inicio
  AND d.dtemissao <= :data_fim
