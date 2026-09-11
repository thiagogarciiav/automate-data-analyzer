# 🗄️Data Analyzer

Projeto Python para centralizar dados de arquivos **CSV, TXT, XML e SQL** em um banco SQLite e gerar uma análise automática.

## Recursos

- Importa CSV e TXT delimitados (detecta automaticamente vírgula, ponto e vírgula, tabulação ou `|`);
- Importa XML tabular, convertendo cada elemento-filho do nó raiz em uma linha;
- Executa arquivos SQL no banco SQLite (útil para esquemas, inserts ou consultas preparatórias);
- Infere tipos `INTEGER`, `REAL` e `TEXT`;
- Gera perfil por tabela: total de linhas, nulos, distintos, mínimos, máximos, média e exemplos;
- Produz relatórios em JSON e CSV.

## Requisitos

Python 3.10 ou superior. Não há bibliotecas externas.

## Uso rápido
1. Clone ou faça o download deste repositório
```bash
git clone https://github.com/thiagogarciiav/automate-data-analyzer.git
```

2. No terminal do VS Code, entre na pasta raiz (`automate-data-analyzer`) e rode:
```powershell
python -m data_analyzer --input .\examples --database .\dados.db --report-dir .\relatorios
```

3. Para importar caminhos específicos:

```powershell
python -m data_analyzer --input vendas.csv clientes.xml schema.sql
```

> Arquivos `.sql` são executados. Use apenas scripts confiáveis.

---
### Contribuição
- Se você quiser contribuir para este projeto, fique à vontade para fazer um fork, criar um branch e enviar um pull request com suas melhorias.

---
### Autor
 Este projeto foi desenvolvido por **Thiago Garcia**.