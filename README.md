# cataloge_ns

Este repositorio proporciona un catalogo local de ejemplos XML para SDF de NetSuite.

## Contenido

- `examples/sdf-objects/`: ejemplos XML minimos por objeto SDF soportado.
- `docs/oracle-netsuite-sdf/object-definitions.md`: indice de objetos con atributos, campos, campos estructurados, features y URL oficial de Oracle.
- `docs/oracle-netsuite-sdf/topic-examples.md`: ejemplos publicados en las paginas tematicas consultadas.
- `tools/fetch_oracle_sdf_docs.py`: extractor para regenerar el catalogo desde Oracle NetSuite Online Help.

## Regenerar

```bash
python3 tools/fetch_oracle_sdf_docs.py
```

El extractor consulta las URLs oficiales de Oracle indicadas en `object-definitions.md` y vuelve a escribir los ejemplos locales.
