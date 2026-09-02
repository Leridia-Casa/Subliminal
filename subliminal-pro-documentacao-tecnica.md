# Subliminal Pro — Documentação Técnica do Código

> Guia didático de como o `subliminal_pro.py` está estruturado por dentro. Pensado para quem vai ler, entender e modificar o código. Acompanhe junto com o arquivo aberto.

---

## Como ler esta documentação

O programa inteiro vive em um único arquivo Python de cerca de 1250 linhas. Pode parecer muito, mas a estrutura é limpa e dividida em blocos com responsabilidades bem definidas. Esta documentação segue a mesma ordem do arquivo, de cima para baixo, explicando o que cada bloco faz, por que ele existe e como ele conversa com os outros.

Uma boa forma de estudar é abrir o código ao lado e ir descendo junto com as seções abaixo.

---

## 1. Mapa geral do arquivo

O arquivo está organizado em sete grandes blocos, nesta ordem:

1. **Imports e flags.** Bibliotecas usadas e a detecção opcional do pystray.
2. **Constantes.** Paleta de cores, biblioteca de frases padrão e configuração padrão.
3. **Funções de sistema.** Detecção de monitores e de processos (Loom, reuniões, Print Screen) via API do Windows.
4. **Classe StatsDB.** Toda a parte de banco de dados SQLite.
5. **Classe Overlay.** A janela transparente que pisca as mensagens.
6. **Classe Tray.** O ícone e o menu na bandeja do sistema.
7. **Classe App.** O cérebro do programa, que junta tudo e contém as seis abas e a lógica principal.

No final há a função `main()`, que cria a janela e inicia o programa.

A lógica de dependências entre os blocos é simples: a classe App usa todas as outras. As outras classes (StatsDB, Overlay, Tray) são independentes entre si e não conhecem umas às outras. Isso mantém o acoplamento baixo: você pode mexer no banco de dados sem tocar na janela de flash, por exemplo.

---

## 2. Imports e a flag do pystray

No topo do arquivo, além das bibliotecas padrão (tkinter, threading, json, sqlite3, ctypes, etc.), há um bloco importante:

```python
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False
```

Esse padrão é uma escolha de robustez. O pystray e o Pillow são as únicas dependências externas. Se a pessoa não as instalou, o programa não quebra: a variável `HAS_TRAY` vira `False` e a funcionalidade de bandeja é simplesmente desativada, enquanto todo o resto continua funcionando. É uma forma elegante de tornar um recurso opcional.

---

## 3. Constantes

### Paleta de cores

```python
BG = "#0d0d1a"; BG2 = "#1a1a2e"; BG3 = "#16213e"; CARD = "#1e1e3a"
ACC = "#7c3aed"; ACC2 = "#3b82f6"; GREEN = "#10b981"; RED = "#ef4444"
YELL = "#f59e0b"; FG = "#e2e8f0"; DIM = "#64748b"; BOR = "#2d2d5b"
```

Centralizar as cores em constantes no topo é o que dá consistência visual ao programa inteiro e facilita trocar o tema. Se você quiser mudar a cor de destaque de roxo para verde, muda só a constante `ACC` e o programa todo acompanha. `BG` são os fundos (do mais escuro ao mais claro), `ACC` são as cores de destaque, `FG` é o texto e `DIM` é o texto secundário.

### A biblioteca de frases (DEFAULT_LIBRARY)

É um dicionário grande que define as oito categorias e suas frases. A estrutura de cada categoria é:

```python
"🎯 Foco & Concentração": {
    "weight": 20, "active": True,
    "messages": [
        {"text": "Minha mente está completamente focada", "weight": 10},
        ...
    ]
}
```

Três coisas a entender aqui:

- **`weight` da categoria** controla a frequência geral daquela categoria aparecer.
- **`active`** liga ou desliga a categoria inteira.
- Cada mensagem tem seu próprio **`weight`**, que controla a frequência dela dentro da categoria.

Esse desenho de pesos em dois níveis (categoria e mensagem) é o que alimenta o sistema de seleção ponderada mais adiante. Para adicionar uma categoria nova de fábrica, basta copiar esse bloco e mudar o conteúdo.

### A configuração padrão (DEFAULT_CONFIG)

Um dicionário que reúne todos os valores iniciais do programa: a biblioteca, tempo de exibição, intervalo, fonte, cores, posição, modo de monitor, flags de pausa automática e a lista de metas.

Esse dicionário é a fonte da verdade dos padrões. Quando o programa abre pela primeira vez e não existe arquivo de configuração salvo, é ele que entra em ação. Quando existe um arquivo salvo, o programa parte deste padrão e sobrescreve com o que foi salvo, garantindo que campos novos sempre tenham um valor mesmo em configurações antigas.

---

## 4. Funções de sistema (a parte que conversa com o Windows)

Este bloco é o mais avançado do programa, porque chama funções do sistema operacional diretamente.

### Detecção de monitores

```python
def get_monitors():
    ...
    windll.user32.EnumDisplayMonitors(None, None, PROC(cb), 0)
```

O tkinter sozinho não enxerga bem múltiplos monitores. A solução é chamar a função `EnumDisplayMonitors` da API do Windows via ctypes. As classes `_RECT` e `_MONINFO` definidas logo acima são traduções em Python de estruturas de dados do Windows, necessárias para receber as informações de cada monitor (posição, tamanho e se é o principal).

A função usa um callback: para cada monitor encontrado, o Windows chama a função interna `cb`, que lê os dados daquele monitor e os adiciona à lista. No final, há um plano B: se a chamada falhar por qualquer motivo, a função retorna um único monitor com o tamanho da tela padrão, garantindo que o programa nunca quebre por causa disso.

### Detecção de processos

```python
def _tasklist():
    r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], ...)
    return r.stdout.lower()

def is_loom_active():
    return any(x in _tasklist() for x in ["loom.exe", "loom helper"])

def is_meeting_active():
    return any(x in _tasklist() for x in ["zoom.exe", "teams.exe", ...])
```

Para saber se o Loom ou uma ferramenta de reunião estão abertos, o programa roda o comando `tasklist` do próprio Windows (que lista todos os processos) e procura pelos nomes dos executáveis no resultado. É uma abordagem leve e sem dependências: não precisa de bibliotecas pesadas de monitoramento de sistema.

### Detecção do Print Screen

```python
def is_printscreen():
    return bool(ctypes.windll.user32.GetAsyncKeyState(VK_SNAPSHOT) & 0x8000)
```

Aqui o programa pergunta diretamente ao Windows se a tecla Print Screen está pressionada naquele instante, usando `GetAsyncKeyState`. A operação com `& 0x8000` é uma checagem de bit que verifica se a tecla está fisicamente pressionada agora.

---

## 5. Classe StatsDB (o banco de dados)

Esta classe encapsula toda a comunicação com o SQLite. O resto do programa nunca escreve SQL diretamente: tudo passa por métodos desta classe. Isso é bom design, porque isola a complexidade do banco em um único lugar.

### Inicialização e a tabela

```python
self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
self.conn.executescript("""
    CREATE TABLE IF NOT EXISTS flash_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL, message TEXT NOT NULL, category TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS i_ts ON flash_log(ts);
""")
```

Existe uma única tabela, `flash_log`, que guarda cada flash com horário, mensagem e categoria. O índice em `ts` (timestamp) acelera as consultas por período, que são as mais frequentes.

Dois detalhes importantes de concorrência:

- **`check_same_thread=False`** permite que o banco seja acessado por threads diferentes. Isso é necessário porque o loop de flashes (que roda em outra thread) grava no banco, enquanto a interface lê dele.
- **`self._lock = threading.Lock()`** é um cadeado. Toda operação de escrita e leitura é envolvida por esse cadeado, garantindo que nunca duas operações aconteçam ao mesmo tempo e corrompam os dados.

### Os métodos de consulta

- **`log(msg, cat)`** registra um flash.
- **`total(period)`** conta o total de flashes em um período.
- **`by_category(period)`** agrupa a contagem por categoria, usado no gráfico de barras.
- **`top_messages(period, limit)`** retorna as mensagens mais exibidas.
- **`timeline(period)`** agrupa por dia (ou por hora, se o período for "hoje"), usado no gráfico de linha.

O método auxiliar `_since(period)` traduz uma palavra como "today", "week" ou "month" na data de corte correspondente, evitando repetir essa lógica em cada consulta.

---

## 6. Classe Overlay (a janela que pisca)

Esta é a classe que efetivamente faz a mágica visual: criar janelas invisíveis que mostram a mensagem por um instante.

### Construção das janelas

No método `_add`, cada janela é criada com uma combinação específica de atributos:

```python
w.overrideredirect(True)            # remove a barra de título
w.wm_attributes("-topmost", True)   # sempre na frente
w.wm_attributes("-disabled", True)  # não captura cliques
```

Essa tríade é o coração do efeito de overlay: uma janela sem moldura, sempre visível por cima de tudo, mas que deixa o usuário clicar nas janelas atrás dela normalmente.

Para a transparência, há dois caminhos dependendo da configuração:

```python
if cfg["use_transparent_bg"]:
    w.configure(bg=self._TRANS)
    w.wm_attributes("-transparentcolor", self._TRANS)
```

A constante `_TRANS = "#010203"` é uma cor-chave: o Windows torna invisível qualquer pixel exatamente dessa cor. Como ela é um tom de preto quase impossível de aparecer por acaso, o fundo da janela some completamente e só o texto fica visível, flutuando sobre a tela.

### O método flash

```python
def flash(self, text):
    ...
    for w, lbl in self.wins:
        lbl.config(text=text)
        lbl.place(relx=rx, rely=ry, anchor="center")
        w.deiconify()
        w.after(int(self.config["display_time"]), w.withdraw)
```

Aqui está o detalhe de eficiência mais importante do programa. Para exibir uma mensagem, ele:

1. Atualiza o texto do rótulo que já existe (não cria um novo).
2. Posiciona o rótulo na tela conforme a configuração.
3. Mostra a janela com `deiconify`.
4. Agenda o desaparecimento com `after`, escondendo a janela com `withdraw` após o tempo definido.

O ponto-chave é usar `withdraw` (esconder) em vez de destruir a janela. Recriar janelas a cada flash gastaria muita memória e processamento. Esconder e mostrar a mesma janela é leve e rápido. Em configurações de múltiplos monitores, o laço repete o processo para cada janela.

---

## 7. Classe Tray (a bandeja do sistema)

Uma classe pequena que cuida do ícone na bandeja. Ela só age se o pystray estiver instalado (lembra da flag `HAS_TRAY`).

O ícone é desenhado em tempo real com o Pillow (um círculo roxo com as letras "SP"), e o menu oferece três ações: mostrar a janela, pausar e sair. O ícone roda em sua própria thread para não bloquear o programa.

Um detalhe importante: todas as ações do menu usam `self.app.root.after(0, ...)`. Isso porque o menu da bandeja roda em outra thread, e mexer na interface diretamente de outra thread causa erros. O `after(0, ...)` agenda a ação de volta na thread principal, de forma segura. Esse mesmo padrão aparece em vários pontos do programa e é um dos conceitos mais importantes para entender o código.

---

## 8. Classe App (o cérebro do programa)

Esta é a maior classe e o centro de tudo. Ela cria a interface, gerencia o estado e contém a lógica principal. Vamos por partes.

### Inicialização (`__init__`)

O construtor monta o programa na ordem certa: carrega a configuração, detecta os monitores, abre o banco de dados, prepara a bandeja, inicializa as variáveis de estado (se está rodando, o evento de parada, o contador de flashes) e então constrói a interface e inicia a bandeja.

As variáveis de estado merecem atenção:

```python
self.running = False              # o programa está exibindo flashes?
self._stop_evt = threading.Event() # sinal para parar a thread do loop
self._flash_cnt = 0               # quantos flashes já aconteceram
self._last_proc = 0               # controle de tempo da checagem de processos
self._proc_pause = False          # resultado da última checagem de processos
```

### Configuração (load, save, collect)

Três métodos cuidam da persistência:

- **`_load_cfg`** lê o arquivo JSON salvo. O truque está em partir do `DEFAULT_CONFIG` e sobrescrever com o que foi salvo (`m.update(saved)`). Isso garante que, se você adicionar um campo novo ao programa no futuro, configurações antigas não quebrem: o campo novo vem do padrão.
- **`_collect`** lê os valores atuais de todos os controles da interface e os joga de volta no dicionário de configuração. É chamado antes de salvar ou iniciar.
- **`_save_cfg`** chama o collect e grava o dicionário no arquivo JSON.

### Estilo (`_setup_style`)

Configura o tema escuro dos widgets ttk (as abas, principalmente). Usa o tema base "clam" e sobrescreve as cores para combinar com a paleta do programa.

### Construção da interface (`_build_ui`)

Cria o Notebook (o conjunto de abas) e adiciona as seis abas, cada uma construída por seu próprio método. Depois monta a barra inferior com os botões de iniciar e salvar e o contador de flashes.

Os métodos auxiliares `_h`, `_lbl`, `_btn` e `_card` são pequenas fábricas de widgets padronizados. Em vez de repetir as mesmas configurações de cor e fonte em cada botão, esses helpers criam widgets já estilizados. É o que mantém o código das abas mais enxuto.

---

## 9. As seis abas em detalhe

### Aba 1: Mensagens (`_tab_messages`)

Dividida em duas colunas. À esquerda, a lista de categorias com um controle de frequência (slider de peso) e um checkbox de ativação. À direita, as mensagens da categoria selecionada, cada uma também com seu slider de peso, mais os botões de adicionar, editar e remover.

A lógica de seleção funciona assim: quando você clica numa categoria (`_on_cat_sel`), a coluna da direita se atualiza para mostrar as mensagens daquela categoria. Quando você ajusta um slider, o método correspondente (`_save_cat_w`, `_save_msg_w`) grava o novo peso direto no dicionário de configuração. Tudo é editado ao vivo na estrutura de dados.

### Aba 2: Tempo (`_tab_timing`)

Dois sliders principais: tempo de exibição (10 a 500ms) e intervalo entre flashes (500 a 60000ms). Logo abaixo, a escolha do modo de ordem (aleatória ponderada, sequencial ou aleatória simples) e os três checkboxes de pausa automática (Loom, reuniões, Print Screen).

Todos os controles chamam `self._apply()` quando mudam, o que aplica as mudanças imediatamente, sem precisar reiniciar.

### Aba 3: Aparência (`_tab_appearance`)

A aba mais rica visualmente. À esquerda, os controles: fonte, tamanho, negrito, cor do texto, fundo transparente ou colorido, opacidade e posição. À direita, um Canvas que mostra um preview ao vivo de como a mensagem vai aparecer.

O método `_draw_preview` é interessante: ele redesenha a prévia sempre que algo muda, escalando o tamanho da fonte para caber no espaço do preview e desenhando o texto com uma leve sombra para dar profundidade. Toda vez que você mexe num controle, o preview se atualiza na hora.

### Aba 4: Monitores (`_tab_monitors`)

Oferece os três modos de exibição (principal, todos, selecionar) e desenha um diagrama visual dos monitores detectados num Canvas. O método `_draw_monitors` faz um trabalho de escala: pega as posições e tamanhos reais dos monitores (que podem ser números grandes como 1920 ou 3840) e os reduz proporcionalmente para caber no diagrama, mantendo o layout fiel à disposição real das telas.

### Aba 5: Estatísticas (`_tab_stats`)

Mostra cards de resumo (total de flashes, hoje, categoria top), dois gráficos e a lista das cinco mensagens mais exibidas.

O ponto técnico notável aqui é que os gráficos são desenhados à mão no Canvas, sem nenhuma biblioteca de gráficos:

- **`_draw_cat_chart`** desenha barras horizontais, calculando a largura de cada barra proporcionalmente ao valor máximo.
- **`_draw_timeline`** desenha um gráfico de área com linha: calcula os pontos, desenha a área preenchida com um polígono semitransparente, traça a linha por cima e marca cada ponto com um círculo.

Construir gráficos assim, do zero, é mais trabalhoso que usar uma biblioteca, mas dá controle total sobre o visual e evita uma dependência pesada como o matplotlib, mantendo o programa leve.

### Aba 6: Metas (`_tab_goals`)

Lista de objetivos pessoais, cada um com checkbox de conclusão e marcador opcional de prioridade. O detalhe que conecta esta aba ao resto do programa está no método `_get_goal_messages`: ele transforma cada meta não concluída em uma mensagem subliminar, que depois entra no rodízio com peso alto. É assim que suas metas viram afirmações que piscam na tela.

---

## 10. A lógica principal (o coração funcional)

Esta é a parte mais importante para entender como o programa realmente funciona. São poucos métodos, mas é onde tudo acontece.

### Montagem do conjunto de mensagens (`_pool`)

```python
def _pool(self):
    items, weights = [], []
    for cat, data in self.config.get("library", {}).items():
        if not data.get("active", True): continue
        cw = data.get("weight", 10)
        for m in data.get("messages", []):
            items.append((m["text"], cat))
            weights.append(cw * m.get("weight", 10))
    for txt, cat in self._get_goal_messages():
        items.append((txt, cat)); weights.append(80)
    return items, weights
```

Este método monta duas listas paralelas: as mensagens elegíveis e seus pesos. Ele percorre as categorias ativas, e para cada mensagem calcula o peso final multiplicando o peso da categoria pelo peso da mensagem. Depois adiciona as metas com peso fixo alto (80). Essas duas listas alimentam a seleção ponderada.

### O loop principal (`_loop`)

```python
def _loop(self):
    order = self.config.get("order", "weighted_random")
    seq_idx = 0
    while not self._stop_evt.is_set():
        items, weights = self._pool()
        if items and not self._should_pause():
            if order == "weighted_random":
                msg, cat = random.choices(items, weights=weights)[0]
            elif order == "random":
                msg, cat = random.choice(items)
            else:
                msg, cat = items[seq_idx % len(items)]
                seq_idx += 1
            self.root.after(0, lambda m=msg, c=cat: self._fire(m, c))
        self._stop_evt.wait(self.config["interval"] / 1000)
```

Este é o motor do programa, e ele roda em uma thread separada. O laço continua enquanto o evento de parada não for acionado. A cada volta:

1. Monta o conjunto de mensagens.
2. Verifica se deve pausar.
3. Se liberado, seleciona uma mensagem conforme o modo escolhido. No modo ponderado, `random.choices` com a lista de pesos faz a mágica de escolher respeitando as frequências.
4. Agenda a exibição na thread principal com `self.root.after(0, ...)`.
5. Espera o intervalo configurado antes da próxima volta.

Dois pontos críticos aqui. Primeiro, o uso de `self._stop_evt.wait(intervalo)` em vez de `time.sleep`: a diferença é que o `wait` pode ser interrompido imediatamente quando o programa é parado, enquanto o sleep deixaria a thread presa até o fim do tempo. Segundo, o `lambda m=msg, c=cat`: capturar os valores como argumentos padrão do lambda evita um bug clássico de closures em laços, garantindo que cada flash use a mensagem correta.

### A verificação de pausa (`_should_pause`)

```python
def _should_pause(self):
    now = time.time()
    if now - self._last_proc > 10:
        self._last_proc = now
        pause = False
        if self.config.get("auto_pause_loom") and is_loom_active(): pause = True
        if self.config.get("auto_pause_meeting") and is_meeting_active(): pause = True
        self._proc_pause = pause
    if self.config.get("auto_pause_ps") and is_printscreen():
        return True
    return self._proc_pause
```

Aqui há uma otimização inteligente de desempenho. Checar processos com o `tasklist` é uma operação relativamente cara, então o programa não faz isso a cada flash. Em vez disso, ele guarda o resultado e só refaz a checagem de processos a cada dez segundos (`now - self._last_proc > 10`). Já a checagem do Print Screen, que é instantânea e barata, é feita a cada chamada, porque o Print Screen precisa de resposta imediata.

### O disparo (`_fire`)

```python
def _fire(self, msg, cat):
    if not self.running or not self.overlay: return
    self.overlay.flash(msg)
    self.db.log(msg, cat)
    self._flash_cnt += 1
    self.lbl_count.config(text=f"{self._flash_cnt} flashes")
    self.tray.tip(f"Subliminal Pro — {self._flash_cnt} flashes")
```

Este método roda na thread principal (foi agendado pelo loop) e faz quatro coisas: exibe a mensagem pela janela de overlay, registra o flash no banco de dados, incrementa o contador e atualiza a interface e a dica da bandeja. É o ponto onde a ação do loop vira efeito visível e dado salvo.

### Iniciar e parar (`_start`, `_stop`)

O `_start` coleta a configuração, monta o pool, verifica se há mensagens, cria as janelas de overlay, atualiza os botões e dispara a thread do loop. O `_stop` faz o caminho inverso: aciona o evento de parada, destrói as janelas de overlay e restaura os botões. A simetria entre os dois é o que mantém o estado sempre consistente.

---

## 11. O modelo de threads (como tudo se comunica)

Este é o conceito mais importante para não se perder no código. O programa tem essencialmente duas threads:

- **A thread principal**, onde vive toda a interface gráfica. O tkinter exige que toda manipulação de tela aconteça aqui.
- **A thread do loop**, criada como daemon, que fica selecionando mensagens e marcando o ritmo.

A regra de ouro é: a thread do loop nunca mexe na tela diretamente. Sempre que ela precisa exibir algo, ela agenda a ação na thread principal usando `self.root.after(0, ...)`. Esse padrão aparece no loop, na bandeja e em vários outros pontos, e é o que mantém o programa estável. Mexer na interface de outra thread é uma das causas mais comuns de travamentos em aplicativos com tkinter, e o programa evita isso de forma disciplinada.

O fato de a thread do loop ser daemon também é importante: significa que ela morre automaticamente quando o programa fecha, sem segurar o sistema. Isso, somado ao tratamento correto do fechamento da janela em `on_close`, evita o problema clássico (que o Subliminal Blaster original tinha) de impedir o Windows de desligar.

---

## 12. O fluxo completo de uma única mensagem

Para amarrar tudo, vale seguir o caminho de uma mensagem do início ao fim:

1. A thread do loop acorda após o intervalo.
2. Ela chama `_pool` e recebe a lista de mensagens elegíveis com seus pesos.
3. Ela chama `_should_pause` e confirma que não há gravação, reunião ou Print Screen em andamento.
4. Ela seleciona uma mensagem com `random.choices`, respeitando os pesos.
5. Ela agenda `_fire` na thread principal e volta a dormir.
6. Na thread principal, `_fire` chama `overlay.flash`, que mostra a janela com o texto.
7. A janela agenda o próprio desaparecimento após o tempo de exibição.
8. `_fire` registra o flash no banco via `db.log` e atualiza o contador.
9. O ciclo recomeça.

Todo o programa é, no fundo, esse ciclo rodando indefinidamente, cercado pela interface que permite configurá-lo e pelo banco que o registra.

---

## 13. Como modificar e estender

Alguns pontos de partida práticos para quem quer mexer no código:

**Adicionar uma categoria de fábrica:** copie um bloco dentro de `DEFAULT_LIBRARY` e troque o conteúdo. Para ela aparecer, delete o arquivo de configuração salvo (ou adicione a categoria pela própria interface).

**Mudar o tema de cores:** altere as constantes de cor no topo. Trocar `ACC` muda a cor de destaque em todo o programa.

**Adicionar um novo app à pausa automática:** inclua o nome do executável na lista dentro de `is_meeting_active` ou crie uma função nova nos moldes dela.

**Suportar imagens além de texto:** seria uma extensão maior. O ponto de entrada seria a classe Overlay, trocando o rótulo de texto por um componente que também aceite imagens, e a estrutura de mensagens, que precisaria distinguir texto de caminho de imagem.

**Adicionar um novo tipo de gráfico:** crie um método de desenho nos moldes de `_draw_cat_chart` e adicione um Canvas para ele na aba de estatísticas.

**Agendar por horário (só exibir em certas horas):** o lugar natural seria o método `_should_pause`, adicionando uma verificação do horário atual contra uma faixa configurável.

---

## 14. Pontos delicados a ter cuidado

Se for modificar o código, atenção redobrada nestes lugares:

- **Qualquer atualização de interface a partir do loop ou da bandeja** precisa passar por `self.root.after(0, ...)`. Esquecer isso causa travamentos difíceis de diagnosticar.
- **Operações no banco** já estão protegidas pelo cadeado dentro da classe StatsDB. Se adicionar métodos novos, mantenha o padrão de envolver o acesso no `with self._lock`.
- **As estruturas `_RECT` e `_MONINFO`** espelham estruturas do Windows. Não mude os campos sem entender o que representam, ou a detecção de monitores quebra.
- **O encerramento em `on_close`** precisa parar o loop, salvar a configuração, fechar o banco e parar a bandeja, nessa lógica. Pular uma dessas etapas pode deixar processos pendurados ou perder dados.

---

## Resumo da arquitetura em uma frase

O Subliminal Pro é uma classe central (App) que orquestra três serviços independentes (banco de dados, janela de flash e bandeja), coordenando uma thread de interface e uma thread de loop que se comunicam de forma segura, tudo configurável por uma interface de seis abas e persistido em arquivo. Entender essa frase é entender o programa.
