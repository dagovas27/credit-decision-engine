# Motor de Decisión Crediticia (`credit-decision-engine`)

## Contexto

- **Dueño:** Daniel Enrique Vásquez González, estudiante de Ingeniería en Inteligencia Artificial y Ciencia de Datos (UPB, Medellín).
- **Propósito:** proyecto de portafolio MLOps / Data Engineering orientado a fintech europeas y a la práctica profesional de 2027.
- **Qué hace:** predice la probabilidad de default (PD) de cada préstamo hipotecario y decide aprobar o rechazar maximizando el beneficio esperado bajo un límite de pérdida, sobre una arquitectura Medallion en Databricks.
- **Ventana:** 16 nov 2026 – 15 ene 2027 (8.5 semanas). Semanas 6 y 7 (Navidad, Año Nuevo) van a media carga.

## Datos

- **Ubicación local (fuera del repo):** `~/Documents/data/freddie_mac/`
- **Contenido:** carpetas `sample_2005` … `sample_2026` (Freddie Mac Single-Family Loan-Level Dataset, archivos de muestra), más `file_layout_july_2026.xlsx` y `user_guide.pdf`.
- Cada carpeta debería traer un archivo de originación y uno de desempeño mensual (servicing). **Verifica los nombres reales** antes de asumirlos.
- Los archivos vienen **sin encabezados y separados por `|`**. El esquema sale de `file_layout_july_2026.xlsx`; contrasta siempre el número de columnas real con el layout.
- `sample_2026` (y probablemente 2025 y 2024) son cosechas incompletas: no tienen 24 meses de desempeño observado.

**Reglas sobre los datos (no negociables):**

- **Nunca** copiar datos crudos al repositorio ni hacerles commit. Los términos de Freddie Mac prohíben redistribuirlos. `.gitignore` debe cubrir cualquier carpeta de datos.
- El README explica cómo descargar los datos; no los incluye.

## Arquitectura

| Capa | Tabla | Contenido |
| --- | --- | --- |
| Bronze | `bronze.loan_origination_raw` | Originaciones tal cual, con `_ingest_ts`, `_source_file`, `_vintage` |
| Bronze | `bronze.loan_performance_raw` | Desempeño mensual, ingerido en micro-batches con Auto Loader |
| Silver | `silver.loans` | Tipado, deduplicado, validado (FICO 300–850, rangos de LTV y DTI) |
| Silver | `silver.loan_status_history` | SCD Type 2 sobre morosidad, servicer y modificaciones |
| Silver | `silver.dq_quarantine` | Registros que fallan validaciones |
| Gold | `gold.loan_features` | Feature table en Unity Catalog, llave `loan_id`, solo información disponible al originar |
| Gold | `gold.default_labels` | Default si, dentro de 24 meses desde el primer pago, lo primero que ocurre es estado ≥ 03, `RA` o código de cierre 02, 03, 09 o 15; un prepago previo cuenta como no default (ADR 0001). Etiqueta principal: ajustada por forbearance/desastre; la original queda como sensibilidad |
| Gold | `gold.vintage_performance` | Curvas de default por cosecha |
| Decisión | `gold.credit_decisions` | Decisión, PD, beneficio esperado, versión del modelo |

**Capa prescriptiva:** `E[π_i] = (1 − PD_i)·m_i·EAD_i − PD_i·LGD_i·EAD_i`; la cartera se elige con una optimización binaria (PuLP u OR-Tools) que maximiza Σ x_i·E[π_i] sujeto a Σ x_i·PD_i·LGD_i·EAD_i ≤ L_max. La LGD se estima con los campos de pérdida real del dataset. La PD debe estar calibrada.

**Validación:**

- Split temporal: entrenamiento 2005–2015, validación 2016–2018, prueba 2019 en adelante, **solo con cosechas que tengan 24 meses de desempeño completos** (verificar la última fecha de reporte en los archivos).
- Las cosechas recientes sin ventana completa se usan para simular "datos nuevos de producción": micro-batches y monitoreo de drift.
- Métrica de negocio: beneficio total del motor frente a la regla base "aprobar si FICO ≥ X".

**Stack:** Databricks (Unity Catalog, Auto Loader, Lakeflow Declarative Pipelines, MLflow, Lakehouse Monitoring, Workflows), Databricks Asset Bundles, Python, pytest, GitHub Actions. Antes de usar una función de Databricks, confirma que el plan del workspace la incluye.

**Workspace:** Databricks Free Edition. Solo cómputo serverless (sin clusters propios), un SQL warehouse 2X-Small, un pipeline de Lakeflow activo por tipo, máximo 5 tareas de job concurrentes, sin ubicaciones de almacenamiento propias y una cuota diaria de uso que apaga el cómputo si se supera. La consola no admite control automatizado del navegador: el trabajo con Databricks se hace por CLI y bundle.

## Estructura del repositorio

```
credit-decision-engine/
├── CLAUDE.md
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── databricks.yml              # Asset Bundle
├── resources/                  # definiciones YAML de jobs y pipelines
├── src/credit_engine/
│   ├── schemas/                # esquemas de originación y desempeño, desde el file layout
│   ├── bronze/
│   ├── silver/
│   ├── gold/
│   ├── ml/
│   ├── decision/
│   └── monitoring/
├── notebooks/                  # solo exploración; nunca lógica de producción
├── scripts/                    # subir datos al Volume, simular llegadas mensuales
├── tests/
├── docs/
│   ├── PROGRESS.md             # estado del proyecto, se actualiza al final de cada sesión
│   ├── architecture.md
│   └── decisions/              # registros de decisiones de diseño (ADR)
└── .github/workflows/ci.yml
```

## Reglas de trabajo

- **Idioma:** conversa conmigo en español. Código, comentarios, commits, README y documentación en `docs/` van en inglés (el portafolio apunta a mercados angloparlantes).
- **Al iniciar cada sesión:** lee este archivo y `docs/PROGRESS.md`, y dime en qué semana estamos y qué sigue.
- **Al cerrar cada sesión:** actualiza `docs/PROGRESS.md` con lo hecho, lo pendiente y las decisiones tomadas.
- **Una semana del roadmap a la vez.** No adelantes trabajo de semanas futuras sin preguntarme.
- **Lógica en `src/`**, probada con pytest. Los notebooks son para explorar.
- **Commits pequeños** con Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`). Corre los tests antes de cada commit.
- **Pregúntame antes de:** hacer push, desplegar o subir algo a Databricks, borrar archivos o tablas, o instalar dependencias nuevas que no estén en este documento.
- **Credenciales:** la autenticación de Databricks y GitHub la hago yo. Nunca pidas, escribas ni guardes tokens en el código o en el chat.
- **Si algo del plan no es viable** (por ejemplo, una limitación del workspace), detente, explícame por qué y propón alternativas antes de seguir.
- **Explícame las decisiones de diseño en 2–3 frases.** Soy estudiante y quiero entender el porqué, no solo tener el código.

## Roadmap

| Semana | Fechas | Entregable | Terminado cuando |
| --- | --- | --- | --- |
| 1 | 16–22 nov | Cimientos: datos inspeccionados, repo, catálogo `credit` (esquemas `bronze`, `silver`, `gold`, `ml`), Volume `landing`, bundle | Los archivos están en el Volume y el bundle despliega un job vacío |
| 2 | 23–29 nov | Bronze con Auto Loader; script que suelta un mes de desempeño a la vez | Un archivo nuevo aparece en Bronze y repetir la corrida no duplica filas |
| 3 | 30 nov–6 dic | Silver: tipado, expectations con cuarentena, SCD2, tests | Un test confirma dos versiones correctas para un préstamo con cambio de estado |
| 4 | 7–13 dic | Gold: etiquetas sin fuga, feature table, desempeño por cosecha | La tasa de default por cosecha muestra el pico de 2006–2007 |
| 5 | 14–20 dic | Logística de base + LightGBM, calibración, MLflow, alias `champion` | AUC, Brier y curva de calibración out-of-time registrados en MLflow |
| 6 | 21–27 dic (ligera) | LGD, beneficio esperado, optimización, `gold.credit_decisions` | Beneficio del motor frente a la regla FICO en cosechas de prueba |
| 7 | 28 dic–3 ene (ligera) | Monitoreo de drift (Lakehouse Monitoring o PSI propio) | El reporte detecta el cambio de 2008 o del COVID |
| 8 | 4–10 ene | Workflow end-to-end + GitHub Actions (pytest y despliegue del bundle) | Un push dispara tests y despliegue sin pasos manuales |
| 8.5 | 11–15 ene | README con diagrama y resultados en dinero, video demo de 3 min | Alguien externo entiende el proyecto leyendo solo el README |

Orquestación y CI/CD nunca se sacrifican: si hay atrasos, se recorta en otra parte.
