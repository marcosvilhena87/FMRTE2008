# F24 — Critérios de suficiência de evidências e protocolo de revisão humana

> **PLANEJAMENTO INICIAL / DOCUMENTAÇÃO / SOMENTE OFFLINE.**
> Este documento **não** comprova observações históricas B03, não aceita riscos residuais, não constitui uma deliberação humana, não aprova mapas de jogadores, não habilita leitura operacional de processos e não autoriza merge ou alteração de `FM2008.mapping`.

## 1. Linha de base e decisões que NÃO foram tomadas

- Repositório de implementação: `marcosvilhena87/FMRTE.2008`; F23.1–F23.4 integrado por *Squash and merge* do PR #24 na `main@f1d44eb17e803d5f7281bb36ac1df0b65b325c75`.
- Quatro workflows pós-merge da `main` verificados como `completed/success`: protótipo Windows `44835345768`, diagnóstico somente leitura `44835345770`, testes do leitor x86 `44835345866`, simulação de memória x86 `44835345809`.
- Artefato pós-merge da simulação: `14678920149`, ZIP SHA-256 `8187e413b670e163024709c0f2ec3b46dd252ba28911f4b92c64b64f66419e6e`. Hash e CI **não** autenticam coleta observacional passada.
- Fonte documental congelada: `marcosvilhena87/FM2008.mapping@df5be0493a1ac7be57208ff0e91c2d7193dfec73`; somente referências, nunca alterações neste repositório.
- Insumos canônicos: `F21B03Evidence.json` (R01–R07); `F22ApprovalGates.json` (G1–G5, A01–A12); `F23B03ProvenanceGaps.json`; `F23ResidualRisks.json` (RA-01–RA-08); `F23HumanDecisionNotMade.json` (`NOT_MADE`); `F23ConsolidatedEvidence.json` (vínculos + cinco hashes).
- Invariantes obrigatórios durante **todo** F24: `NoApprovedPlayerMaps`, `approved=false`, `operational=false`, `B03=PENDING-DECLARED`, `A12=GATE-BLOQUEADO`, `decision=NOT_MADE`, `reviewer=null`, `reviewedAt=null`, oito riscos não aceitos, `approvedPlayerMaps=0`.
- Proibidos `fm.exe` operacional, escrita de memória/save, WPF live, promoção de offsets ou novos mapas aprovados. Sucesso no CI, Git author, timestamp, estado do PR e revisão de código **não** são aprovação humana nem evidência histórica.

## 2. Objetivo e fronteira do F24

Definir **o que seria necessário para considerar um dossiê documental suficientemente rastreável para ser apresentado a um revisor humano**, sem converter essa elegibilidade em resultado de avaliação, aceite de risco ou habilitação operacional.

**Três estados diferentes, nunca confundidos**:
1. **Integridade técnica**: arquivo existe, compromisso SHA-256 corresponde, estrutura fechada válida, referência e CI do mesmo HEAD rastreáveis. Pode ser verificada automaticamente.
2. **Suficiência documental proposta**: completude e qualidade de fontes primárias avaliadas explicitamente, com ressalvas e capacidade de auditoria; o mecanismo automático pode **identificar lacunas**, mas não atribuir autenticidade à observação histórica.
3. **Decisão humana**: somente um ato humano posterior, distinto, assinado ou documentalmente atribuível, com competência, escopo, data, versão das fontes e avaliação de riscos. F24 **não realiza esse ato**.

O status inicial do conjunto é `INSUFFICIENT_PRESERVED`; o sistema pode descrever pendências, nunca concluir `APPROVED` ou `OPERATIONAL`.

## 3. Critérios de suficiência B03 por observação R01–R07

Para cada observação, propor cinco itens de proveniência como **requisitos a comprovar**, não como campos já preenchidos:

| Critério | Evidência primária ou comprovação necessária | Reprovação/bloqueio por padrão |
| --- | --- | --- |
| P01 — autoria | Identidade atribuível do executor original e vínculo explícito com o registro | Autor Git, ator de workflow, nome em comentário ou identidade não confirmada |
| P02 — temporalidade | Data/hora da observação e contexto de sessão, com fonte primária datada verificável | Timestamp editorial/CI ou reconstrução retroativa |
| P03 — ambiente | Versão/build, plataforma e contexto relevante da sessão, declarados e corroboráveis | Inferência automática a partir da máquina de CI |
| P04 — método | Procedimento observacional suficientemente descrito, limites da amostra e vinculação ao resultado | Descrição genérica, sem cadeia entre observação e documento |
| P05 — corroboração | Evidência externa independente **quando disponível**, ou ausência explicitamente declarada | Confundir checksum, reprodução offline ou existência no Git com corroboração histórica |

Para cada R01–R07, registrar no futuro uma avaliação `MISSING` / `DECLARED_UNCORROBORATED` / `DOCUMENTED_UNREVIEWED` / `REVIEW_REQUIRED`; **nenhum desses rótulos equivale a `VERIFIED`**. Qualquer preenchimento original de `executor`, `observedAt`, `environment`, `collectionMethod` ou `externalCorroboration` requer autorização, fonte primária verificável e revisão distinta. Os manifestos históricos congelados continuam com `null`.

### Matriz de suficiência contextual (sem novas observações)

- **R01/R02**: identidade de build e contexto declarado, evitando tratar base preferencial como prova de relocação natural.
- **R03/R04**: vínculo da amostra relatada aos resultados de ID/nome; não extrapolar uma amostra à tabela completa, nem inferir componentes de nomes não verificados.
- **R05/R06**: separar passagem temporal e reinício natural declarados de interrupções reais durante leitura, ABA e encerramento anômalo.
- **R07**: identificar as duas partidas/saves relatados e os limites de generalização; não considerar múltiplos registros equivalentes a uma observação independente auditada.

**Regra fail-closed:** uma observação com P01–P04 não comprovados, fonte original não verificável ou contradição relevante permanece pendente. P05 ausente é uma limitação expressa e deve ser examinada por uma pessoa; nunca é substituída por CI.

## 4. Critérios de revisão dos portões G1–G5 e riscos RA-01–RA-08

| Portão | Critérios | Riscos relacionados no F22 | Questão de suficiência |
| --- | --- | --- | --- |
| G1 | A01, A02 | RA-01, RA-06 | Identidade de build/instância e limites de base/relocação documentados? |
| G2 | A03, A04, A05, A10 | RA-05 | Amostragens e nomes com cadeia de proveniência e limites explícitos? |
| G3 | A06, A07, A08 | RA-02, RA-03, RA-04 | Separados ensaios offline e relatos naturais sobre consistência e recuperação? |
| G4 | A09, A11 | RA-07, RA-08 | Fronteiras de somente leitura, variantes e offsets não aprovados preservadas? |
| G5 | A12 | Transversal aos RA-01–RA-08 | Existe decisão humana **independente**? No F24: **não**. |

Todos os RA-01–RA-08 devem aparecer nominalmente com origem, impacto documental, informação ainda não comprovada, evidência de suporte e `riskAccepted=false`; **sem atribuir probabilidade ou aceite inventados**. A ausência de risco no registro, referência trocada, conflito entre portões ou decisão implicada deve bloquear a validação.

## 5. Protocolo para uma revisão humana futura (descrição, não execução)

A futura revisão, se solicitada em outro marco autorizado, deverá:
1. Confirmar identidade e competência do revisor, sua independência da coleta/automação e eventuais conflitos de interesse.
2. Fixar o escopo e as versões exatas do dossiê por SHA-256, commit do repositório de trabalho e revisão da fonte documental.
3. Separar evidências originais R01–R07, relatos, inferências e resultados de CI; enumerar lacunas B03 sem completá-las com metadados editoriais.
4. Avaliar individualmente os portões G1–G5 e critérios A01–A12, registrando incertezas e documentação insuficiente.
5. Examinar RA-01–RA-08 separadamente, sem aceite implícito, e justificar eventual necessidade de novas evidências.
6. Produzir registro de conclusão *somente quando uma autorização expressa e processo humano real existirem*, com data, identidade, decisão, escopo e referências; qualquer recusa ou devolução para complementação deve ser igualmente rastreável.
7. Tratar a eventual decisão humana como distinta de implementação/merge: **nenhum ato documental habilita automaticamente qualquer recurso operacional**.

**Template F24 obrigatório:** `reviewer=null`, `reviewedAt=null`, `authorityReference=null`, `decision=NOT_MADE`, `approved=false`, `operational=false`; campos de aceite dos oito riscos permanecem `false` e referências de aceite `null`.

## 6. Plano de implementação em fases

### F24.1 — Inventário estruturado de suficiência

Criar um JSON canônico e esquema fechado com R01–R07 × P01–P05, referências a fontes congeladas, hashes e estados de lacuna; distinguir integridade de documentos da autenticidade histórica. Testes negativos contra metadados falsificados, omissão e troca de observação, aprovação indevida, campos extras e mutações de SHA. Nenhum campo primário do F21 é completado neste marco.

### F24.2 — Matriz de elegibilidade documental e riscos

Vincular P01–P05, G1–G5/A01–A12 e RA-01–RA-08 ao inventário de F24.1 e às fontes F22/F23.2. Exigir que todos os riscos continuem não aceitos. Testes de fonte divergente, ausência de risco, falseamento de comprovação e fechamento indevido do portão A12.

### F24.3 — Protocolo e decisão humana `NOT_MADE`

Criar formulário/registro **não preenchido** e respectivo contrato fechado: revisor/data/competência/referência de decisão `null`; riscos não aceitos; CI e estado de PR não substituem revisão humana. Testes negativos contra decisão fictícia, revisor de CI, data do commit, falsos aceites e qualquer promoção a operacional.

### F24.4 — Encadeamento de evidências de CI e revisão final

Gerar manifesto de proveniência do próprio CI com `runId`, `runAttempt`, `event`, `checkoutSha`, `prHeadSha` e hashes, relatórios estruturados por teste e verificações negativas independentes. Diferenciar checkout de HEAD em `pull_request`; ZIP e digest públicos demonstram integridade do CI, não autenticidade histórica. Executar quatro workflows `push` e quatro `pull_request`; revisar artefatos, hashes, logs Windows e regressões antes de propor Ready. Sem merge sem autorização específica.

## 7. Critérios de aceite do PLANEJAMENTO F24

- Documento existe na branch do novo PR **Draft**, criado a partir do commit pós-merge F23 validado.
- F24.1–F24.4, P01–P05, R01–R07, G1–G5, A01–A12 e RA-01–RA-08 estão mapeados sem falsa suficiência.
- Não se infere proveniência histórica de Git/CI; nenhuma fonte histórica é alterada.
- Todos os registros humanos permanecem não decididos; nenhum teste sinaliza autorização humana real.
- Código, conectividade operacional, mapa de jogadores e `FM2008.mapping` não são modificados por este plano.
- PR permanece **Draft** e sem merge até revisão técnica posterior e autorização expressa.

**Estado F24:** planejamento documental inicial; **nenhuma implementação F24.1–F24.4, revisão humana de fato ou aprovação operacional foi executada**.
