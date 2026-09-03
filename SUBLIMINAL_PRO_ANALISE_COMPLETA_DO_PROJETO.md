# Subliminal Pro — Análise Completa do Projeto, Código e Arquitetura

> **Relatório Técnico e Gerencial Exaustivo**  
> Este documento apresenta o entendimento completo do projeto **Subliminal Pro**, abrangendo a análise de todo o código-fonte, necessidades de negócio e técnicas, soluções arquiteturais adotadas, histórico e diagnóstico dos principais erros/desafios enfrentados, a lista completa de ferramentas, métodos e recursos utilizados, bem como considerações sobre empacotamento, distribuição e diretrizes de uso.

---

## 1. Visão Geral e Entendimento do Projeto

### 1.1. O que é o Subliminal Pro?
O **Subliminal Pro** é uma aplicação desktop nativa para Windows 11/10 desenvolvida em Python. O seu objetivo principal é exibir mensagens de afirmação positiva na tela em intervalos configuráveis por frações de segundo (geralmente entre 10ms e 33ms). 

Esse tempo de exposição extremamente curto permite que a mensagem seja visualizada de forma limiar/subliminar sem interromper a atenção consciente do usuário, que pode continuar trabalhando, estudando, programando ou navegando na internet normalmente.

### 1.2. Origem e Evolução (Subliminal Blaster vs. Subliminal Pro)
O projeto foi concebido como uma recriação e evolução moderna de softwares clássicos da década de 2000, notadamente o *Subliminal Blaster*. As principais melhorias introduzidas pelo Subliminal Pro incluem:
- **Interface Gráfica Moderna (Dark Mode):** Substituição das interfaces cinzas e antiquadas do Windows XP por um layout escuro em 6 abas temáticas construído com Tkinter/ttk.
- **Banco de Dados Relacional e Estatísticas:** Monitoramento detalhado e persistente de todas as exibições (*flashes*) em banco SQLite com gráficos gerados dinamicamente.
- **Seleção Ponderada de Mensagens:** Algoritmo de dois níveis (Categoria x Mensagem) que substitui a simples escolha sequencial/aleatória.
- **Integração com Metas Pessoais:** Transformação automática de metas cadastradas em afirmações subliminares com alta prioridade no rodízio.
- **Pausa Automática Inteligente:** Detecção proativa de ferramentas de gravação de tela (Loom), salas de reunião (Zoom, Teams, Meet, Discord) e teclas de captura (*Print Screen*) para evitar que mensagens vazem em apresentações ou vídeos.
- **Suporte Multi-Monitor Naitvo:** Identificação geométrica e posicionamento perfeito em múltiplos monitores via chamada direta à Win32 API.

### 1.3. Estrutura de Arquivos e Componentes da Solução

```
files (5)/
│
├── subliminal_pro.py            # Aplicação principal completa (~1.250 linhas, UI Pro 6 abas, SQLite, Win32)
├── subliminal.py                # Versão Lite/Fundação (~540 linhas, MVP focado em Tkinter puro)
│
├── build_icon.py                # Script utilitário para geração dinâmica do icon.ico multi-resolução
├── build.py                     # Script de empacotamento automatizado via PyInstaller
├── SubliminalPro.spec           # Arquivo de especificação técnica do PyInstaller
├── installer.iss                # Script de compilação do instalador Windows via Inno Setup
│
├── config.json                  # Arquivo de configuração da versão Lite
├── subliminal_config.json       # Persistência de configurações e acervo Pro (57 frases em 8 categorias)
├── subliminal_stats.db          # Banco de dados SQLite local com histórico e log de flashes
│
├── subliminal-pro-projeto.md    # Guia do desenvolvedor e visão geral
└── subliminal-pro-documentacao-tecnica.md # Documentação linha a linha da versão Pro
```

---

## 2. Análise Detalhada do Código-Fonte

O repositório é composto por dois módulos executáveis principais (`subliminal.py` e `subliminal_pro.py`) e uma suíte de automação de build.

### 2.1. Módulo `subliminal_pro.py` (Arquitetura Pro)
O arquivo `subliminal_pro.py` é estruturado em 7 blocos funcionais com baixíssimo acoplamento:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        App (Orquestrador Central)                      │
├───────────────┬────────────────┬─────────────────┬─────────────────────┤
│   StatsDB     │    Overlay     │      Tray       │   Funções Win32     │
│ (SQLite Log)  │ (Janela Flash) │ (System Tray)   │ (Monitores/Procs)   │
└───────────────┴────────────────┴─────────────────┴─────────────────────┘
```

1. **Imports e Flags de Robustez:**  
   Importação condicional do `pystray` e `Pillow` usando a flag `HAS_TRAY`. Se as dependências de bandeja não estiverem instaladas, a aplicação inicia normalmente desabilitando apenas o minimizado para a bandeja.
2. **Constantes e Sistema de Cores:**  
   Definição da paleta *Dark Mode* (`#0d0d1a`, `#1a1a2e`, `#7c3aed`, etc.), da biblioteca padrão (`DEFAULT_LIBRARY` com 8 categorias e 57 mensagens ponderadas) e das configurações padrão (`DEFAULT_CONFIG`).
3. **Funções de Integração com o Windows (Win32 API):**  
   - `get_monitors()`: Mapeia as posições e dimensões físicas das telas usando `EnumDisplayMonitors` com estruturas `_RECT` e `_MONINFO`.
   - `is_loom_active()` / `is_meeting_active()`: Monitora a tabela de processos ativas via `tasklist`.
   - `is_printscreen()`: Checa instantaneamente a tecla Print Screen via `GetAsyncKeyState(VK_SNAPSHOT)`.
4. **Classe `StatsDB` (Persistência e Análise):**  
   Gerencia o SQLite local (`subliminal_stats.db`). Cria a tabela `flash_log` e o índice temporal `i_ts`. Utiliza thread locking (`threading.Lock`) e `check_same_thread=False` para garantir acesso seguro a partir de múltiplas threads.
5. **Classe `Overlay` (Gerenciador da Janela Subliminar):**  
   Instancia janelas transparentes, sem bordas (`overrideredirect(True)`), sempre no topo (`-topmost`) e passíveis de clique através (`-disabled`). Reutiliza as janelas com `withdraw()` e `deiconify()` para evitar *overhead* de alocação de memória.
6. **Classe `Tray` (Menu na Bandeja do Sistema):**  
   Gera dinamicamente um ícone no System Tray com menu para restaurar janela, pausar/retomar e encerrar a aplicação.
7. **Classe `App` (Cérebro da Aplicação):**  
   Gerencia a janela principal Tkinter em 6 abas:
   - **💬 Mensagens:** CRUD de frases, sliders de peso por categoria/mensagem e controle de frequências.
   - **⏱ Tempo:** Ajuste de tempo de visibilidade (10-500ms), intervalo entre exibições, modo de seleção e checkboxes de pausa automática.
   - **🎨 Aparência:** Seleção de fontes, tamanhos, cores, transparência, opacidade, posição do texto e pré-visualização em tempo real (*Canvas Preview*).
   - **🖥 Monitores:** Seleção de monitor ativo (Principal, Todos ou Específicos) com diagrama gráfico proporcional.
   - **📊 Estatísticas:** Cards numéricos e gráficos nativos desenhados no `tk.Canvas` (gráfico de barras por categoria e gráfico de linha/área temporal).
   - **🎯 Metas:** Gerenciador de objetivos pessoais que injeta automaticamente afirmações com peso elevado (80) no ciclo de flashes.

---

## 3. Necessidades do Projeto e Soluções Adotadas

| Necessidade do Projeto | Desafio Técnico Associado | Solução Adotada no Código |
| :--- | :--- | :--- |
| **Exibir texto relâmpago sem atrapalhar o uso do PC** | Janelas padrão do SO capturam foco do teclado/mouse, roubando o clique do usuário. | Atributos `wm_attributes("-disabled", True)`, `overrideredirect(True)` e transparência por cor-chave (`-transparentcolor #010203`). |
| **Suporte a múltiplos monitores com resoluções mistas** | O `winfo_screenwidth()` do Tkinter lê apenas a tela primária. | Mapeamento nativo com Win32 API via `ctypes.windll.user32.EnumDisplayMonitors` criando overlays individuais posicionados. |
| **Evitar travamentos ou gargalo de CPU** | Destruir e recriar janelas/labels a cada flash consome CPU e gera *garbage collection* excessivo. | Reutilização de instâncias das janelas `Toplevel` e `Label`, apenas alternando o estado entre `deiconify()` e `withdraw()`. |
| **Pausa automática em videochamadas/gravações** | Evitar vazamento de mensagens subliminares em gravações do Loom ou reuniões no Zoom/Teams. | Polling otimizado via `subprocess` chamando `tasklist` a cada 10s (cache) e captura imediata de Print Screen com `GetAsyncKeyState`. |
| **Comunicação segura entre Threads** | A thread de background do loop não pode alterar componentes visuais do Tkinter diretamente. | Uso rigoroso de `root.after(0, func)` para agendar modificações de GUI na Main Thread do Tkinter. |
| **Concorrência no Banco de Dados** | A thread do loop grava dados no SQLite no momento exato em que a thread principal lê para atualizar gráficos. | Implementação de `threading.Lock()` no `StatsDB` e abertura da conexão com `check_same_thread=False`. |
| **Visualização de Estatísticas Leve** | Incluir bibliotecas como `matplotlib` aumentaria o executável em +50MB e o uso de RAM. | Desenvolvimento de um motor de renderização gráfico personalizado desenhado a mão no `tk.Canvas` do Tkinter. |

---

## 4. Diagnóstico de Erros e Desafios Enfrentados

### Erro #1: Travamento do Windows ao Desligar o Computador
- **Contexto:** O software original (*Subliminal Blaster*) apresentava um *bug* clássico no qual o Windows ficava preso na tela de "Encerrando" caso o aplicativo estivesse rodando.
- **Causa Raiz:** Threads em segundo plano mantidas abertas sem o sinalizador de encerramento automático (`daemon`) e falta de interceptação do evento `WM_DELETE_WINDOW`.
- **Solução Adotada:** 
  1. Criação das threads com `daemon=True` (`threading.Thread(..., daemon=True)`).
  2. Implementação do método `on_close()` vinculado a `root.protocol("WM_DELETE_WINDOW", app.on_close)`. O método aciona o `Event` de parada, destrói os overlays, encerra a bandeja do Pystray e fecha o banco SQLite de forma limpa.

### Erro #2: Crashes por Acesso Concorrente de UI (Tkinter Thread Safety)
- **Contexto:** Exceções aleatórias do Tkinter informando `main thread is not in main loop` ou congelamento da interface ao clicar nos itens do menu da bandeja.
- **Causa Raiz:** O Pystray e o loop de temporização rodam em threads separadas da thread visual do Tkinter.
- **Solução Adotada:** Encapsulamento de todas as chamadas de alteração de GUI via `self.root.after(0, lambda: ...)`. O método `after(0)` transfere a execução da função para a fila de eventos da thread principal de forma thread-safe.

### Erro #3: Alto Uso de Processador (Picos de CPU por Polling)
- **Contexto:** Em testes preliminares, a checagem contínua de processos com `tasklist` a cada 500ms causava uso elevado de CPU (15%-25%).
- **Causa Raiz:** A execução de um processo filho via `subprocess.run(["tasklist"...])` duas vezes por segundo é extremamente onerosa para o SO.
- **Solução Adotada:** *Throttling* inteligente na função `_should_pause()`. A verificação do `tasklist` foi isolada com um temporizador de 10 segundos (`now - self._last_proc > 10`), enquanto a verificação leve de hardware (Print Screen via `GetAsyncKeyState`) continua ocorrendo instantaneamente em cada flash.

### Erro #4: Incompatibilidade de Escala e Resolução Multi-Monitor
- **Contexto:** Em monitores com escala de DPI diferente (ex: 100% no Monitor 1 e 125% no Monitor 2), a posição da mensagem ficava deslocada.
- **Solução Adotada:** Utilização dos retângulos físicos absolutos retornados pela Win32 API (`rcMonitor.left`, `rcMonitor.top`, `rcMonitor.right`, `rcMonitor.bottom`) para calcular com exatidão a geometria de cada janela `Toplevel`.

---

## 5. Lista Completa de Ferramentas, Métodos e Recursos Utilizados

### 5.1. Linguagem e Runtime
- **Python 3.8+ (64-bit):** Linguagem principal de desenvolvimento, escolhida pelo ecossistema rico e portabilidade nativa no Windows.

### 5.2. Módulos da Biblioteca Padrão do Python (Sem instalação necessária)
- `tkinter` & `ttk`: Construção de janelas, abas (Notebook), campos, sliders e estilização com tema `clam`.
- `sqlite3`: Banco de dados relacional embutido sem necessidade de servidor externo.
- `ctypes`: Interface de chamadas nativas em C para a Win32 API (`user32.dll`).
- `threading`: Controle de concorrência com `Thread`, `Event` e `Lock`.
- `subprocess`: Execução do Utilitário de linha de comando `tasklist` do SO.
- `json`: Leitura e escrita de arquivos de configuração local (`subliminal_config.json`).
- `random`: Seleção amostral ponderada (`random.choices`) e aleatória simples (`random.choice`).
- `os`, `sys`, `time`, `datetime`: Manipulação de caminhos, sistema operacional e formatação temporal.

### 5.3. Dependências Externas (Instaladas via `pip`)
- `pystray` (v0.19+): Biblioteca para criação e controle de ícones no System Tray do Windows.
- `Pillow / PIL` (v9.0+): Manipulação de imagem em memória para desenhar o ícone da aplicação e gerar a suíte de ícones `icon.ico`.
- `pyinstaller` (v5.0+): Compilador e empacotador que transforma os scripts Python em um executável nativo do Windows `.exe`.

### 5.4. Ferramentas de Empacotamento e Distribuição
- **Inno Setup 6:** Compilador de instaladores para Windows. Utilizado pelo arquivo `installer.iss` para gerar o instalador `SubliminalPro_Setup.exe` com compactação LZMA2 e instalação no diretório local do usuário (`{localappdata}`), dispensando privilégios de Administrador.

### 5.5. Métodos e Padronizações Arquiteturais
- **Algoritmo de Seleção Ponderada em Dois Níveis:**  
  $$\text{Peso Final} = \text{Peso}_{\text{Categoria}} \times \text{Peso}_{\text{Mensagem}}$$
- **Design Pattern Helper / Factory:** Métodos auxiliares `_h()`, `_lbl()`, `_btn()`, `_card()` para instanciação padronizada de componentes de UI.
- **Engine Gráfica em Canvas Nativo:** Cálculo trigonométrico e vetorial direto no `tk.Canvas` para geração de barras e polígonos preenchidos com efeito de transparência visual.

---

## 6. Guia de Compilação, Empacotamento e Implantação

Para gerar a versão executável final e o instalador redistribuível a partir do código-fonte, siga os passos abaixo no ambiente Windows:

### Passo 1: Preparar o Ambiente Python
```bash
# 1. Instalar as dependências necessárias
pip install pystray pillow pyinstaller
```

### Passo 2: Gerar o Executável Standalone (.exe)
Execute o script de build automatizado:
```bash
python build.py
```
*O script irá gerar o ícone `icon.ico` multi-resolução e compilar a aplicação para a pasta `dist/SubliminalPro.exe`.*

### Passo 3: Compilar o Instalador Windows (Inno Setup)
1. Instale o [Inno Setup](https://jrsoftware.org/isdl.php).
2. Abra o arquivo `installer.iss` no Inno Setup Compiler.
3. Clique em **Compile** (ou execute no terminal: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`).
4. O arquivo final de instalação estará disponível em `installer_output/SubliminalPro_Setup.exe`.

---

## 7. Análise Científica, Validação e Segurança de Uso

### 7.1. Validação Científica e Expectativa Realista
Estudos em neurociência e psicologia cognitiva (utilizando fMRI) confirmam que estímulos visuais subliminares abaixo do limiar de percepção consciente ativam estruturas cerebrais como a amígdala e o córtex pré-frontal. No entanto, é crucial alinhar expectativas:
- Mensagens subliminares atuam como **reforço de intenção pré-existente** e **gatilho cognitivo**.
- Não produzem alterações de comportamento contrárias à vontade do indivíduo.
- A ferramenta deve ser compreendida como um auxílio contínuo de baixo esforço mental para complementar o foco e a determinação consciente do usuário.

### 7.2. Alertas de Segurança Médica
> [!CAUTION]
> **Aviso de Fotossensibilidade e Epilepsia:**  
> Devido à natureza de exibição de *flashes* rápidos de luz e texto na tela, o uso deste aplicativo **NÃO É RECOMENDADO** para pessoas que possuam histórico de epilepsia fotossensível, enxaqueca ocular ou sensibilidade extrema a estímulos visuais piscantes.

---

## 8. Conclusão e Próximos Passos Sugeridos

O **Subliminal Pro** representa um exemplo notável de engenharia de software em Python para desktop. Ele combina integração de baixo nível com o SO Windows, arquitetura concorrente limpa e uma experiência visual atraente sem a necessidade de *runtimes* pesados (como Electron ou Chromium).

### Sugestões para Futuras Versões:
1. **Suporte a Imagens e Afirmações Visuais:** Permitir que o `Overlay` pisque imagens PNG com transparência além de textos.
2. **Agendamento por Horários:** Adicionar regras de tempo para atuar apenas durante o expediente de trabalho (ex: 09h às 18h).
3. **Sincronização em Nuvem:** Possibilidade de backup e sincronização das frases e estatísticas via Google Drive ou Dropbox.
