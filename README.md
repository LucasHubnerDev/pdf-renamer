# PDF Renamer

Ferramenta de linha de comando que lê os PDFs de uma pasta, identifica o tipo de
cada documento (fatura, boleto, nota fiscal etc.), extrai os dados relevantes e
renomeia os arquivos automaticamente, sempre com prévia e confirmação antes de
qualquer alteração.

## Como funciona

O programa conduz um fluxo de 9 etapas:

1. Seleção da pasta com os PDFs
2. Informação do período (data inicial/final dos documentos)
3. Escolha dos tipos de documento a processar
4. Escolha dos campos a extrair e da ordem deles no nome
5. Leitura e análise dos PDFs
6. Prévia das alterações (tabela original -> novo nome)
7. Confirmação do usuário
8. Renomeação dos arquivos
9. Relatório do processamento (.txt na própria pasta)

### Pipeline de extração

```text
PDF
 └─ possui texto nativo?
     ├─ SIM  -> extração direta de texto (pypdf)
     └─ NÃO  -> páginas convertidas em imagem (300 dpi) -> OCR (Tesseract)
                └─ texto extraído
                    └─ classificação por regras de palavras-chave
                        └─ extração de campos (regex)
                            └─ filtro de tipo e período
                                └─ prévia -> confirmação -> renomear -> relatório
```

A data usada no filtro de período vem do conteúdo do próprio documento
(emissão, vencimento, competência...), nunca da data de modificação do sistema
de arquivos. Quando a data não é encontrada, o programa avisa o usuário.

### Camadas do sistema

| Camada | Módulos | Responsabilidade |
|---|---|---|
| Leitura | `extraction/` | Detectar texto nativo x escaneado e extrair o texto |
| OCR | `extraction/ocr/` | Motor de OCR atrás de interface abstrata (troca fácil) |
| Classificação | `classification/` | Regras configuráveis em `config.py` |
| Campos | `fields/` | Extração de número, cliente, datas, valores etc. via regex |
| Renomeação | `renaming/` | Normalização de nomes, duplicados e execução segura |
| Interface | `ui.py` | Menus, prévia e confirmação no terminal |
| Relatório | `report.py` | Resumo no console + `.txt` para auditoria |

Garantias de segurança: nenhum arquivo é renomeado antes da confirmação;
nomes duplicados ganham sufixo `(1)`, `(2)`; um PDF com erro não interrompe o
lote; tudo roda localmente, nenhum documento sai da máquina.

## Estrutura do projeto

```text
pdf_renamer/
├── main.py                  # Orquestra as 9 etapas
├── config.py                # Regras, campos e políticas (painel de controle)
├── models.py                # Estruturas de dados compartilhadas
├── report.py                # Relatório do processamento
├── ui.py                    # Interação com o usuário
├── extraction/
│   ├── text_extractor.py    # Texto nativo (pypdf)
│   ├── pdf_reader.py        # Orquestra texto direto ou rasterizar + OCR
│   └── ocr/
│       ├── base.py          # Interface abstrata do OCR
│       ├── factory.py       # Registro de motores
│       └── tesseract_engine.py
├── classification/
│   ├── rules.py             # Estrutura de uma regra
│   └── classifier.py        # Motor de pontuação por palavras-chave
├── fields/
│   └── extractors.py        # Extração de campos por regex
└── renaming/
    ├── normalizer.py        # Sanitização de nomes de arquivo
    └── renamer.py           # Planejar + executar renomeação
```

## Dependências

### Software

| Dependência | Versão | Para quê |
|---|---|---|
| Python | 3.10 ou superior | Executar o programa |
| Tesseract OCR | 5.x | Reconhecimento de texto em PDFs escaneados |
| Poppler | versão recente | Converter páginas do PDF em imagem para o OCR |

### Pacotes Python (via pip)

| Pacote | Função |
|---|---|
| pypdf | Leitura de texto nativo de PDFs |
| pdf2image | Rasterização das páginas (usa o Poppler) |
| pytesseract | Ponte Python -> Tesseract |
| Pillow | Manipulação de imagens |

## Instalação no Windows (passo a passo)

Compatível com Windows 10 e 11. Todos os comandos abaixo funcionam no PowerShell.

### Passo 1 — Instalar o Python

1. Baixe o instalador em https://www.python.org/downloads/
2. Execute o instalador e **marque a caixa "Add python.exe to PATH"** antes de
   clicar em "Install Now". Sem isso o terminal não reconhece o comando `python`.
3. Abra um novo PowerShell e verifique:

```powershell
python --version
```

Deve responder algo como `Python 3.12.x`. Se não reconhecer, reinstale marcando
a caixa do PATH (ou use `py --version`, o launcher do Windows).

### Passo 2 — Criar a pasta do projeto

```powershell
mkdir pdf_renamer
cd pdf_renamer
mkdir extraction\ocr, classification, fields, renaming
ni main.py, config.py, models.py, report.py, ui.py
ni extraction\__init__.py, extraction\text_extractor.py, extraction\pdf_reader.py
ni extraction\ocr\__init__.py, extraction\ocr\base.py, extraction\ocr\factory.py, extraction\ocr\tesseract_engine.py
ni classification\__init__.py, classification\rules.py, classification\classifier.py
ni fields\__init__.py, fields\extractors.py
ni renaming\__init__.py, renaming\normalizer.py, renaming\renamer.py
```

(`ni` é o apelido de `New-Item`; os `__init__.py` ficam vazios, eles apenas
marcam as pastas como pacotes Python.)

### Passo 3 — Colar o código

Abra a pasta no VS Code (`code .`) e cole o conteúdo de cada módulo no arquivo
correspondente. A primeira linha de cada bloco indica o caminho
(ex.: `# renaming/normalizer.py`).

### Passo 4 — Instalar o Tesseract OCR

1. Baixe o instalador para Windows em https://github.com/UB-Mannheim/tesseract/wiki
2. Durante a instalação, em "Select Components", expanda **Additional language
   data** e marque **Portuguese**.
3. Conclua a instalação. O caminho padrão é `C:\Program Files\Tesseract-OCR`.
4. Adicione esse caminho ao PATH:
   - Tecla Windows -> digite "variáveis de ambiente" -> "Editar as variáveis
     de ambiente do sistema"
   - Botão "Variáveis de Ambiente..." -> em "Variáveis do usuário", selecione
     `Path` -> "Editar..."
   - "Novo" -> cole `C:\Program Files\Tesseract-OCR` -> OK em todas as janelas
5. **Feche e reabra o terminal** (o PATH só é recarregado em sessão nova) e verifique:

```powershell
tesseract --version
```

### Passo 5 — Instalar o Poppler

1. Baixe a build para Windows em
   https://github.com/oschwartz10612/poppler-windows/releases
2. Extraia o conteúdo em `C:\poppler` (a pasta interna tem nome tipo
   `poppler-24.02.0`)
3. Adicione ao PATH a pasta `bin` dentro de `Library`, ou seja
   `C:\poppler\poppler-24.02.0\Library\bin` (mesmo procedimento do passo anterior)
4. Reabra o terminal e verifique:

```powershell
pdftoppm -v
```

### Passo 6 — Criar o ambiente virtual e instalar os pacotes

Dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação com erro de política de execução, rode uma
vez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Alternativa pelo cmd: use `.venv\Scripts\activate.bat` em vez do `.ps1`.

### Passo 7 — Verificação final

```powershell
tesseract --version
pdftoppm -v
python -c "import pypdf, pdf2image, pytesseract, PIL; print('dependencias OK')"
```

Os três comandos devem responder sem erro.

## Como executar

Com o ambiente virtual ativado (`.\.venv\Scripts\Activate.ps1`):

```powershell
python main.py
```

O programa pergunta a pasta, o período, os tipos e os campos, mostra a prévia
e só renomeia após você responder `S`:

```text
ARQUIVO ORIGINAL                        NOVO NOME
----------------------------------------   ----------------------------------------
documento001.pdf                            FATURA 1920 LUCAS HUBNER.pdf
scan002.pdf                                 BOLETO 5831 JOAO SILVA.pdf

Deseja executar essas alterações? [S/N]: s
```

Ao final, um `relatorio_AAAAMMDD_HHMMSS.txt` é gravado na própria pasta
processada.

## Configuração

Tudo que costuma mudar de usuário para usuário está em `config.py`:

| Opção | Padrão | Descrição |
|---|---|---|
| `OCR_ENGINE` | `"tesseract"` | Motor de OCR registrado na fábrica |
| `OCR_LANG` | `"por"` | Idioma do Tesseract |
| `OCR_DPI` | `300` | Resolução ao rasterizar páginas escaneadas |
| `MAIUSCULAS` | `True` | Nomes finais em caixa alta |
| `INCLUIR_SEM_DATA` | `True` | Mantém no fluxo PDFs sem data identificada |
| `FIELD_CATALOG` | dicionário | Campos disponíveis no menu |
| `DEFAULT_RULES` | lista | Regras de classificação por palavras-chave |

### Adicionar um tipo de documento

Acrescente uma regra em `DEFAULT_RULES` (config.py). Regras mais específicas
vêm antes na lista:

```python
ClassificationRule(
    tipo="CONTRATO",
    obrigatorias=("contrato",),
    opcionais=("contratante", "contratado", "cláusula"),
),
```

### Adicionar um campo

1. Escreva a função em `fields/extractors.py`;
2. Registre-a no dicionário `FIELD_EXTRACTORS`;
3. Adicione o id em `FIELD_CATALOG` (config.py).

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `tesseract is not installed or it's not in your PATH` | Tesseract fora do PATH | Refaça o passo 4 ou fixe o caminho no código (abaixo) |
| `Unable to get page count` na hora do OCR | Poppler fora do PATH | Refaça o passo 5 |
| `'python' não é reconhecido` | Python sem PATH | Reinstale marcando "Add python.exe to PATH" ou use `py` |
| PowerShell bloqueia `Activate.ps1` | Política de execução | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| OCR ruim em documentos escaneados | Resolução baixa | Aumente `OCR_DPI` para 400 em `config.py` |

Se precisar fixar o caminho do Tesseract no código, adicione no início de
`extraction/ocr/tesseract_engine.py`:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## Linux e macOS (resumo)

```bash
sudo apt install python3-venv tesseract-ocr tesseract-ocr-por poppler-utils  # Debian/Ubuntu
brew install tesseract tesseract-lang poppler                                # macOS
pip install -r requirements.txt
python main.py
```
