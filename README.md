# PROSE NES 2026/2 - Sprint 1

Dashboards por equipe para as devolutivas do Survey Alunos, com historico da Sprint 0 e resultados da Sprint 1.

## Equipes disponibilizadas

| Equipe | Projeto | Supervisor(a) | Periodo | Respostas Sprint 1 |
| --- | --- | --- | --- | --- |
| T1 | Biblioteca do NDH | Marcio | Vespertino | 6/6 (100,0%) |
| T2 | Prontuario Eletronico da Psicologia | Vanessa | Vespertino | 4/6 (66,7%) |
| T3 | Sistema de Gestao de Comissoes | Awdren | Noturno | 4/6 (66,7%) |
| T4 | SIGEMAT | Funabashi | Noturno | 4/6 (66,7%) |
| T5 | Aves do Pantanal | Maria Istela | Vespertino | 3/6 (50,0%) |
| T6 | RCP extra-hospitalar | Vanessa | Vespertino | 6/6 (100,0%) |
| T7 | Notifica Saude | Turine | Noturno | 3/6 (50,0%) |
| T8 | COINS | Maria Istela | Noturno | 2/6 (33,3%) |
| T9 | HPV Conecta | Patricia | Noturno | 3/6 (50,0%) |
| T10 | SCM | Turine | Vespertino | 6/6 (100,0%) |

Publicacao completa atualizada em 02/10/2026: 41 respostas para 60 integrantes (68,3%). Estes totais contam envios classificados por equipe; pseudonimos nao permitem confirmar a identidade individual de cada respondente. A participacao parcial deve ser considerada na interpretacao.

A comparacao contextual usa a media simples dos escores das dez equipes na mesma sprint, incluindo a propria equipe, sem ponderar pelo numero de respostas. Os dez PDFs foram exportados novamente com essa referencia. O T6 passou de cinco para seis respostas apos a confirmacao de uma associacao de nome; os resultados de T1, T3, T9 e T10 permaneceram iguais aos da publicacao anterior.

O semestre 2026/2 tem 60 estudantes, com seis integrantes por equipe. O cadastro do T9 foi corrigido em 28/09/2026, incluindo a resposta anteriormente nao associada de um integrante. A participacao do historico da Sprint 0 do T9 foi corrigida para 4/6 (66,7%), sem alterar suas notas.

## Estrutura

- `common/dashboard_app.py`: motor compartilhado dos dashboards.
- `teams/t1/app.py` ate `teams/t10/app.py`: entradas independentes no Streamlit.
- `teams/tX/data/relatos/`: relatos agregados de cada sprint.
- `pdfs/`: relatorios de devolutiva da Sprint 1.
- `scripts/export_team_pdf.py`: exportador de PDFs a partir dos JSONs agregados locais, com precisao completa.
- `common/pdf_report.py`: modelo aprovado de cinco paginas, derivado do toolkit.
- `docs/metodologia-dashboard.md`: criterios de calculo e interpretacao.

Todos os dez times reutilizam o mesmo motor. O historico da Sprint 0 foi preservado do repositorio anterior.

## Streamlit Community Cloud

Use este repositorio, branch `main`, e uma das entradas:

- T1: `teams/t1/app.py`
- T2: `teams/t2/app.py`
- T3: `teams/t3/app.py`
- T4: `teams/t4/app.py`
- T5: `teams/t5/app.py`
- T6: `teams/t6/app.py`
- T7: `teams/t7/app.py`
- T8: `teams/t8/app.py`
- T9: `teams/t9/app.py`
- T10: `teams/t10/app.py`

Para executar localmente:

```powershell
pip install -r requirements.txt
streamlit run teams/t1/app.py
```

## Exportar PDF

O modelo aprovado tem capa escura e quatro paginas internas claras: resumo,
evolucao SPACE com comparacao contextual, pontos fortes e pontos de atencao.
Nao usar o antigo modelo escuro de seis paginas. Os JSONs de metricas ficam
somente no ambiente local; o PDF publico mostra o total de integrantes, sem nomes.

```powershell
pip install -r requirements-pdf.txt
python scripts/export_team_pdf.py --team T1 --sprint "Sprint 1" --metrics-root ../outputs/nes-sprint1-2026-2/2026-2/teams --output pdfs/relatorio_T1_sprint_1.pdf
python scripts/export_team_pdf.py --team T3 --sprint "Sprint 1" --metrics-root ../outputs/nes-sprint1-2026-2/2026-2/teams --output pdfs/relatorio_T3_sprint_1.pdf
python scripts/export_team_pdf.py --team T6 --sprint "Sprint 1" --metrics-root ../outputs/nes-sprint1-2026-2/2026-2/teams --output pdfs/relatorio_T6_sprint_1.pdf
python scripts/export_team_pdf.py --team T9 --sprint "Sprint 1" --metrics-root ../outputs/nes-sprint1-2026-2/2026-2/teams --output pdfs/relatorio_T9_sprint_1.pdf
python scripts/export_team_pdf.py --team T10 --sprint "Sprint 1" --metrics-root ../outputs/nes-sprint1-2026-2/2026-2/teams --output pdfs/relatorio_T10_sprint_1.pdf
```

## Dados e privacidade

Este repositorio contem apenas relatos agregados e os arquivos necessarios ao dashboard. Nomes de estudantes, planilhas de respostas, auditorias de identificacao e ZIPs locais nao sao publicados. Os ZIPs de importacao sao arquivos de trabalho da pesquisa, nao materiais para distribuicao aos alunos.

Os dados da Sprint 1 foram processados com o schema vigente do toolkit. A alternativa "Totalmente desinteressado" foi reconhecida como nivel 1 da escala de motivacao. Respostas vazias permanecem ausentes, sem imputacao. O item condicional sobre discussao da solucao foi calculado somente com respostas validas; no T7, nao houve respostas nesse item, que foi excluido dos pontos fortes e de atencao, sem receber nota zero. A dimensao Activity nao e calculada nesta versao.
