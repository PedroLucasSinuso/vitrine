SELECT
    c.dscodigo as codigo,
    d.cdprincipal as codigo_chamada
FROM wshop.codigos c
JOIN wshop.detalhe d ON c.iddetalhe = d.iddetalhe;