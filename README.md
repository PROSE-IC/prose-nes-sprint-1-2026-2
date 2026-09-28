# PROSE NES 2026/2 - Sprint 1

Dashboards por equipe para as devolutivas do Survey Alunos, com historico da Sprint 0 e resultados da Sprint 1.

## Equipes disponibilizadas

| Equipe | Projeto | Supervisor(a) | Periodo | Respostas Sprint 1 |
| --- | --- | --- | --- | --- |
| T3 | Sistema de Gestao de Comissoes | Awdren | Noturno | 4/6 (66,7%) |
| T9 | HPV Conecta | Patricia | Noturno | 2/5 (40,0%) |

Esta publicacao inclui somente T3 e T9. A comparacao contextual usa apenas as equipes com dados carregados na sprint escolhida, nao toda a turma. A participacao parcial deve ser considerada na interpretacao.

## Estrutura

- `common/dashboard_app.py`: motor compartilhado dos dashboards.
- `teams/t3/app.py` e `teams/t9/app.py`: entradas independentes no Streamlit.
- `teams/tX/data/relatos/`: relatos agregados de cada sprint.
- `pdfs/`: relatorios de devolutiva da Sprint 1.
- `scripts/export_team_pdf.py`: exportador de PDFs a partir dos relatos agregados.
- `docs/metodologia-dashboard.md`: criterios de calculo e interpretacao.

Os demais times podem ser acrescentados em `teams/tX/`, reutilizando o mesmo motor, sem alterar os dados dos times ja publicados. O historico da Sprint 0 foi preservado do repositorio anterior.

## Streamlit Community Cloud

Use este repositorio, branch `main`, e uma das entradas:

- T3: `teams/t3/app.py`
- T9: `teams/t9/app.py`

Para executar localmente:

```powershell
pip install -r requirements.txt
streamlit run teams/t3/app.py
```

## Exportar PDF

```powershell
pip install -r requirements-pdf.txt
python scripts/export_team_pdf.py --team T3 --sprint "Sprint 1" --output pdfs/relatorio_T3_sprint_1.pdf
python scripts/export_team_pdf.py --team T9 --sprint "Sprint 1" --output pdfs/relatorio_T9_sprint_1.pdf
```

## Dados e privacidade

Este repositorio contem apenas relatos agregados e os arquivos necessarios ao dashboard. Nomes de estudantes, planilhas de respostas, auditorias de identificacao e ZIPs locais nao sao publicados. Os ZIPs de importacao sao arquivos de trabalho da pesquisa, nao materiais para distribuicao aos alunos.

Os dados da Sprint 1 foram processados com o schema vigente do toolkit. A alternativa "Totalmente desinteressado" foi reconhecida como nivel 1 da escala de motivacao. Respostas vazias permanecem ausentes, sem imputacao. A dimensao Activity nao e calculada nesta versao.
