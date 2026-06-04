# cataloge_ns

Este repositorio proporciona un catalogo local de ejemplos XML para SDF de NetSuite.

## Contenido

- `examples/sdf-objects/`: ejemplos XML minimos por objeto SDF soportado.
- `examples/sdf-additional-files/`: archivos adicionales de ejemplo requeridos u opcionales por algunos objetos SDF.
- `docs/oracle-netsuite-sdf/object-definitions.md`: indice de objetos con atributos, campos, campos estructurados, features y URL oficial de Oracle.
- `docs/oracle-netsuite-sdf/topic-examples.md`: ejemplos publicados en las paginas tematicas consultadas.
- `tools/fetch_oracle_sdf_docs.py`: extractor para regenerar el catalogo desde Oracle NetSuite Online Help.

## Regenerar

```bash
python3 tools/fetch_oracle_sdf_docs.py
```

El extractor consulta las URLs oficiales de Oracle indicadas en `object-definitions.md` y vuelve a escribir los ejemplos locales.

## Guia para agentes de IA

Usa este repositorio como catalogo de referencia local antes de proponer o generar XML SDF para NetSuite.

1. Empieza por `docs/oracle-netsuite-sdf/object-definitions.md` para identificar el objeto correcto, su prefijo de `scriptid`, sus atributos, campos, campos estructurados, features requeridas y archivos adicionales.
2. Usa `examples/sdf-objects/<object>.xml` como plantilla inicial, no como XML listo para produccion. Los valores `TODO_*`, `Example *` y referencias como `[scriptid=...]` deben reemplazarse con valores reales del proyecto NetSuite.
3. Revisa `examples/sdf-additional-files/` cuando el objeto indique `Additional files`. Por ejemplo, `advancedpdftemplate` requiere un `.template.xml` y `emailtemplate` puede usar un `.template.html`.
4. Consulta la URL de Oracle enlazada en `object-definitions.md` cuando necesites detalles que no esten modelados en los ejemplos, como valores permitidos, restricciones de longitud o comportamiento de features.
5. Si cambias el extractor o actualizas la fuente de Oracle, regenera el catalogo con `python3 tools/fetch_oracle_sdf_docs.py` y revisa el diff antes de usar los ejemplos.

## Convenciones SDF al crear archivos

Los archivos de `examples/sdf-objects/` estan nombrados por tipo de objeto para que funcionen como catalogo. En un proyecto SDF real, dentro de `Objects/`, debes crear el archivo con el `scriptid` real del objeto. El prefijo correcto esta documentado en la columna `Script ID prefix` de `docs/oracle-netsuite-sdf/object-definitions.md`, extraida de la tabla oficial de Oracle `SDF Custom Object File Structure`.

```text
Objects/customscript_mi_suitelet.xml
Objects/customscript_mi_cliente.xml
Objects/customrecord_mi_registro.xml
Objects/custcenter_mi_centro.xml
```

El contenido del archivo debe conservar el root XML del tipo de objeto y el mismo `scriptid`:

```xml
<suitelet scriptid="customscript_mi_suitelet">
  <name>Mi Suitelet</name>
  <scriptfile>[src=FileCabinet/SuiteScripts/mi_suitelet.js]</scriptfile>
  <defaultfunction>onRequest</defaultfunction>
</suitelet>
```

Para scripts, normalmente se usa `customscript_*` como prefijo del `scriptid` y del nombre del XML del objeto. Para otros objetos no infieras el prefijo: consulta `Script ID prefix`. Por ejemplo, `emailtemplate` usa `custemailtmpl_`, `advancedpdftemplate` usa `custtmpl_`, `savedsearch` usa `customsearch_` y `transactionbodycustomfield` usa `custbody_`.

El archivo JavaScript referenciado por `scriptfile` vive aparte en `FileCabinet/SuiteScripts/...`; el XML de `Objects/` solo define el objeto SDF.

## Validacion local

Valida que los XML sigan siendo bien formados despues de editar o regenerar:

```bash
for f in examples/sdf-objects/*.xml examples/sdf-additional-files/*.template.xml; do xmllint --noout "$f" || exit 1; done
```

Notas importantes:

- Este repositorio documenta estructura y ejemplos; no reemplaza la validacion de SDF contra una cuenta NetSuite.
- Los XML generados son minimos y pueden requerir campos estructurados adicionales segun el caso de uso.
- Mantener las URLs oficiales en el indice ayuda a que otros agentes puedan verificar informacion sensible a cambios de version.
