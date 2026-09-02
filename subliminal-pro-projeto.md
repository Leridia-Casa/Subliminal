# Subliminal Pro — Documentação do Projeto

> Software desktop para Windows 11 que exibe mensagens de afirmação positiva na tela por frações de segundo, expondo-as ao subconsciente enquanto você usa o computador normalmente. Construído em Python, leve e com interface moderna.
>
> Esta página é um guia de projeto voltado para o desenvolvedor: explica o que é, por que vale a pena construir, o que você aprende no caminho e como começar com confiança.

---

## 1. O QUE É ESTE PROJETO? {#p1-oque}

O Subliminal Pro é um aplicativo de desktop para Windows que pisca mensagens de texto na tela por milissegundos, tempo curto o suficiente para o olho mal registrar conscientemente, mas (segundo a teoria do subliminar) tempo suficiente para o subconsciente captar.

É uma versão moderna e turbinada de um software clássico chamado Subliminal Blaster. Enquanto o original tem uma interface dos anos 2000 e recursos básicos, o Subliminal Pro foi reconstruído do zero com interface escura moderna, banco de dados de estatísticas, sistema de metas, suporte a múltiplos monitores e pausa automática inteligente.

Tecnicamente, é um único arquivo Python que roda consumindo pouca memória RAM (entre 40 e 50 MB com os gráficos ativos), usando majoritariamente bibliotecas que já vêm com o Python. O programa fica na bandeja do sistema e trabalha em segundo plano enquanto você faz suas atividades normais: trabalhar, navegar, estudar ou assistir vídeos.

Em resumo: é uma ferramenta de desenvolvimento pessoal, e ao mesmo tempo um projeto de engenharia de software interessante que toca em vários conceitos avançados (concorrência, API do Windows, persistência de dados, visualização de dados feita à mão).

---

## 2. PARA QUE SERVE? {#p1-para-que}

O propósito declarado é a reprogramação mental por repetição: ao expor o subconsciente repetidamente a afirmações como "Minha mente está completamente focada" ou "Sou confiante e seguro de mim mesmo", a ideia é reforçar gradualmente esses estados mentais durante o uso normal do computador.

As mensagens vêm organizadas em oito categorias de desenvolvimento pessoal:

- Foco e concentração
- Confiança e autoestima
- Motivação e produtividade
- Aprendizado acelerado
- Abundância e prosperidade
- Paz e equilíbrio emocional
- Saúde e vitalidade
- Sucesso e realizações

Uma observação importante sobre honestidade: a ciência sobre mensagens subliminares é debatida. Estudos de ressonância magnética mostram que estímulos subliminares de fato ativam regiões cerebrais, mesmo sem a pessoa perceber. Porém, pesquisas sobre comportamento indicam que o efeito é sutil, costuma durar pouco tempo, e funciona melhor quando a mensagem reforça um objetivo que a pessoa já tem conscientemente. Em outras palavras: o subliminar parece funcionar como um reforço de algo que você já quer, não como um interruptor mágico que muda quem você é. A ferramenta faz mais sentido como complemento de um esforço consciente, não como substituto dele.

Além do uso pessoal, o projeto serve como peça de portfólio e exercício de aprendizado. Construir o Subliminal Pro ensina concorrência com threads, integração com a API do Windows, banco de dados embutido, criação de gráficos sem bibliotecas externas e empacotamento de aplicativos desktop.

---

## 3. NÍVEL DE DIFICULDADE {#p1-nivel}

Nível geral: intermediário.

O projeto é totalmente acessível para quem tem fundamentos de Python, mas cada módulo tem uma curva diferente. A divisão por componente ajuda a enxergar onde estão os desafios:

- Janela de overlay transparente: fácil. Poucas linhas com tkinter resolvem.
- Interface de configuração com abas: fácil a intermediário. É repetitivo, mas direto.
- Loop de exibição com threading: intermediário. Exige entender threads e comunicação segura com a interface.
- Banco de dados SQLite com estatísticas: intermediário. SQL básico e cuidado com concorrência.
- Detecção de monitores via ctypes: avançado. Mexe diretamente com a API do Windows.
- Pausa automática (detectar Loom, reuniões, print screen): intermediário a avançado. Envolve leitura de processos do sistema.
- Ícone na bandeja do sistema: intermediário. Depende da biblioteca pystray.
- Gráficos desenhados no Canvas: intermediário. Exige lógica de desenho manual, sem matplotlib.

Quem nunca trabalhou com threads ou com a API do Windows vai aprender bastante nas partes de ctypes e concorrência. O restante é confortável para quem já fez alguns projetos em Python.

---

## 4. FUNCIONALIDADES PRINCIPAIS {#p1-funcionalidades}

O Subliminal Pro entrega um conjunto de recursos bem acima do software original que o inspirou:

**Biblioteca de mensagens inteligente.** Oito categorias com 57 frases pré-carregadas em português, cada uma com peso individual. É possível adicionar, editar e remover frases, ativar ou desativar categorias inteiras, e ajustar a frequência de cada mensagem.

**Sistema de seleção ponderada.** Três modos de exibição: aleatório ponderado (mensagens com peso maior aparecem mais), aleatório simples e sequencial. O peso final combina o peso da categoria com o peso da mensagem.

**Controle fino de tempo.** Tempo de exibição ajustável de 10 a 500 milissegundos e intervalo entre flashes de 500 a 60000 milissegundos.

**Personalização visual completa.** Escolha de fonte, tamanho, negrito, cor do texto, fundo transparente ou colorido, opacidade e posição na tela (centro, topo, base ou aleatória). Tudo com pré-visualização ao vivo enquanto você ajusta.

**Suporte a múltiplos monitores.** Detecção automática dos monitores com diagrama visual. Você escolhe exibir no monitor principal, em todos ou em monitores específicos.

**Estatísticas com banco de dados.** Cada flash é registrado em um banco SQLite. A aba de estatísticas mostra gráficos de barras e de área, top 5 mensagens mais exibidas e filtros por período (hoje, 7 dias, 30 dias, tudo).

**Sistema de metas.** Você cadastra objetivos pessoais com nível de prioridade. Metas ativas entram automaticamente no rodízio de mensagens subliminares com peso alto, transformando seus objetivos em afirmações.

**Pausa automática inteligente.** O programa detecta automaticamente quando o Loom, ferramentas de reunião (Zoom, Teams, Meet, Discord) ou a tecla Print Screen estão em uso, e pausa os flashes para que as mensagens não apareçam em gravações, compartilhamentos de tela ou capturas.

**Bandeja do sistema.** Roda em segundo plano com ícone na bandeja, menu para mostrar a janela, pausar ou sair.

**Persistência de configuração.** Todas as preferências são salvas automaticamente em arquivo e recarregadas ao abrir o programa.

---

## 5. BENEFÍCIOS E IMPACTO DO PROJETO {#p1-beneficios}

Os benefícios se dividem em duas frentes: para quem usa o software e para quem o constrói.

**Para quem usa.** A proposta é manter um fluxo constante de afirmações positivas no campo de visão durante o trabalho, sem exigir tempo dedicado. Diferente de meditação ou journaling, que pedem uma pausa consciente, o subliminar roda em paralelo com suas atividades. Para a pessoa certa, isso pode funcionar como um lembrete sutil e contínuo dos objetivos que ela já está perseguindo.

Sobre o impacto real, vale repetir o que a pesquisa mostra, para a expectativa ficar calibrada. Há evidências de que estímulos subliminares produzem efeitos mensuráveis no cérebro e, em alguns estudos, no desempenho (há pesquisas associando pistas subliminares a melhor desempenho acadêmico e físico). Porém, o consenso é que o efeito é modesto, costuma ser de curta duração e depende de já existir um desejo ou objetivo alinhado à mensagem. O subliminar não cria motivação do nada e não muda comportamentos contra a vontade da pessoa. O honesto é apresentar a ferramenta como um reforço de baixo esforço, e não como uma promessa de transformação garantida.

Um alerta de responsabilidade: por conter padrões de luz piscando, a ferramenta não é recomendada para pessoas com epilepsia ou sensibilidade visual.

**Para quem constrói.** Aqui o impacto é concreto e garantido. Desenvolver este projeto consolida habilidades que aparecem em pouquíssimos tutoriais juntas: programação de interface desktop, concorrência com threads, integração de baixo nível com a API do Windows, banco de dados embutido e visualização de dados construída manualmente. É uma peça de portfólio que demonstra domínio técnico real, não um app CRUD genérico.

---

## 6. STACK TECNOLÓGICA {#p1-stack}

A stack foi escolhida priorizando baixo consumo de RAM e o mínimo de dependências externas. Quase tudo usa a biblioteca padrão do Python.

- **Python 3.8 ou superior:** linguagem base.
- **tkinter:** interface gráfica e janelas de overlay. Já vem com o Python e é muito mais leve que alternativas como PyQt.
- **ttk:** widgets temáticos do tkinter, usados para o visual moderno das abas.
- **sqlite3:** banco de dados embutido para registrar e consultar estatísticas. Também nativo.
- **ctypes:** ponte para chamar funções da API do Windows diretamente, usada na detecção de monitores e na captura da tecla Print Screen. Nativo.
- **threading:** execução do loop de flashes em segundo plano sem travar a interface. Nativo.
- **subprocess:** execução do comando tasklist do Windows para detectar processos como Loom e Zoom. Nativo.
- **json:** leitura e escrita do arquivo de configuração. Nativo.
- **pystray:** criação do ícone e menu na bandeja do sistema. Dependência externa.
- **Pillow (PIL):** geração da imagem do ícone da bandeja. Dependência externa.

Apenas duas bibliotecas precisam ser instaladas separadamente: pystray e Pillow. Todo o resto já acompanha qualquer instalação padrão do Python.

---

## 7. FERRAMENTAS E BIBLIOTECAS NECESSÁRIAS {#p1-ferramentas}

**Ambiente de desenvolvimento:**

- Python 3.8 ou superior instalado no Windows.
- Um editor de código. VS Code é a recomendação por ter bom suporte a Python.
- PyInstaller para empacotar o programa como um arquivo executável (.exe) distribuível, caso você queira compartilhar sem exigir que a pessoa tenha Python.

**Instalação das dependências externas:**

```
pip install pystray pillow
```

**Bibliotecas já incluídas no Python (não precisam de instalação):**

tkinter, ttk, sqlite3, ctypes, threading, subprocess, json, random, os, time, datetime.

**Para gerar o executável final:**

```
pip install pyinstaller
pyinstaller --onefile --windowed subliminal_pro.py
```

O sinalizador onefile gera um único .exe e o windowed evita que abra um terminal junto com o programa.

---

## 8. ARQUITETURA DO SISTEMA {#p1-arquitetura}

O sistema é organizado em classes com responsabilidades bem separadas, o que mantém o código limpo apesar da quantidade de recursos.

**App (orquestrador central).** É o coração do programa. Carrega a configuração, constrói a interface com as seis abas, gerencia o estado (rodando ou parado), coordena o loop de flashes e conecta todas as outras partes. É quem decide quando exibir uma mensagem e qual mensagem exibir.

**Overlay (a janela que pisca).** Responsável por criar uma ou mais janelas transparentes, sempre no topo, sem barra de título e que não capturam cliques do mouse. Quando recebe uma mensagem, ela aparece na posição configurada pelo tempo definido e some. Em configurações com múltiplos monitores, cria uma janela por monitor.

**StatsDB (banco de dados).** Encapsula toda a comunicação com o SQLite. Registra cada flash (mensagem, categoria, horário) e oferece consultas prontas: total de flashes, contagem por categoria, top mensagens e linha do tempo. Usa um bloqueio (lock) para ser seguro com múltiplas threads.

**Tray (bandeja do sistema).** Cria o ícone na bandeja e o menu de contexto, permitindo controlar o programa mesmo com a janela principal minimizada.

**Funções auxiliares.** Fora das classes, funções independentes cuidam de tarefas específicas: detectar monitores via API do Windows, verificar se o Loom está ativo, se há uma reunião em andamento ou se o Print Screen foi pressionado.

**Fluxo de dados.** A configuração vive em um arquivo JSON, é carregada pelo App ao iniciar e salva ao fechar. Quando um flash acontece, o evento flui do loop para o Overlay (que mostra) e para o StatsDB (que registra). Os gráficos da aba de estatísticas leem de volta do StatsDB.

**Modelo de threads.** A interface roda na thread principal. O loop de flashes roda em uma thread separada (daemon) para não travar a tela. A comunicação entre elas é feita de forma segura agendando as atualizações de interface de volta na thread principal, evitando os erros comuns de mexer na interface a partir de outra thread.

---

## 9. FLUXO DE FUNCIONAMENTO {#p1-fluxo}

O ciclo de vida do programa, do clique inicial ao funcionamento contínuo, segue esta sequência:

1. **Inicialização.** O programa abre, carrega a configuração salva (ou usa os padrões na primeira execução) e detecta os monitores disponíveis.

2. **Montagem.** A interface com as seis abas é construída e o ícone da bandeja é iniciado. O programa fica pronto, em estado parado.

3. **Configuração pelo usuário.** A pessoa ajusta mensagens, tempos, aparência, monitores e metas conforme sua preferência. Tudo pode ser pré-visualizado ao vivo.

4. **Início.** Ao clicar em iniciar, o programa monta o conjunto de mensagens elegíveis (combinando categorias ativas e metas), cria as janelas de overlay nos monitores escolhidos e dispara a thread do loop.

5. **Loop de exibição.** Em segundo plano, a cada intervalo configurado, o loop seleciona uma mensagem segundo o modo escolhido (aleatório ponderado, aleatório ou sequencial).

6. **Verificação de pausa.** Antes de exibir, o loop checa se deve pausar: se o Loom está gravando, se há uma reunião ativa ou se o Print Screen foi pressionado. Se sim, pula a exibição naquele ciclo.

7. **Disparo do flash.** Se liberado, a mensagem é exibida na tela pelo tempo configurado e some. O evento é registrado no banco de dados e o contador na barra inferior é atualizado.

8. **Espera e repetição.** O loop aguarda o intervalo e repete o ciclo, indefinidamente, até a pessoa pausar ou parar.

9. **Encerramento.** Ao parar, as janelas de overlay são destruídas. Ao fechar o programa, a configuração é salva, o banco é fechado e a bandeja é encerrada de forma limpa.

---

## 10. FERRAMENTAS SIMILARES NO MERCADO {#p1-similares}

O nicho de software subliminar existe há mais de uma década, mas a maioria das opções está tecnologicamente parada no tempo. Um panorama dos principais:

**Subliminal Blaster (MISPBO Technologies).** O mais conhecido e a inspiração direta deste projeto. Freeware de cerca de 500 KB, exibe mensagens de texto na tela enquanto você usa o PC. Tem categorias editáveis e controle de fonte, cor e transparência. A versão 4 é de desenvolvimento brasileiro. Interface bem datada e, segundo relatos de usuários, com bugs incômodos (um conhecido impede o desligamento do Windows enquanto o programa está aberto).

**Subliminal Flash.** Concorrente direto que também pisca textos rapidamente. Vem com mensagens pré-configuradas para autoestima, desenvolvimento pessoal, parar de fumar e perder peso. Permite editar mensagens e definir posição e intervalo.

**Free Subliminal Text (FST).** Projeto open-source escrito em Java, portanto multiplataforma (Windows, Mac, Linux). Usa flashes rápidos de texto parcialmente transparente em posições aleatórias. Tem controle de fonte, ordem de palavras e posicionamento. Já teve problemas de vazamento de memória ao longo do desenvolvimento.

**Subliminal Message Flasher.** App para Android, fora do universo desktop. Controla velocidade, cor e rotação automática de fontes.

**MB Free Subliminal Message Software e similares.** Diversas ferramentas menores com proposta parecida e execução básica.

**Onde o Subliminal Pro se diferencia.** Comparado a todos esses, o Pro se destaca em vários pontos: interface escura moderna em vez do visual anos 2000, sistema de pesos para priorizar mensagens, estatísticas reais com gráficos e banco de dados, sistema de metas que vira afirmação, suporte nativo a múltiplos monitores e, principalmente, a pausa automática para gravações e reuniões, recurso que nenhum concorrente clássico oferece e que é essencial para quem grava a tela ou faz videochamadas com frequência.

---

## 11. DESAFIOS TÉCNICOS E COMO RESOLVER {#p1-desafios}

Construir o Subliminal Pro envolve resolver alguns problemas técnicos não triviais. Os principais e suas soluções:

**Janela transparente que não bloqueia cliques.** O overlay precisa cobrir a tela inteira, ficar sempre no topo, mas deixar o usuário clicar normalmente nas janelas atrás dele. A solução combina três atributos: remover a borda da janela, defini-la como transparente usando uma cor-chave que vira invisível, e desabilitar a captura de cliques. Assim a mensagem aparece flutuando sem atrapalhar o trabalho.

**Detecção de múltiplos monitores.** O tkinter sozinho não enxerga bem configurações com vários monitores. A solução é chamar diretamente a função da API do Windows que enumera os monitores, via ctypes, obtendo a posição e o tamanho exatos de cada um. Há um plano B que usa o tamanho de tela padrão caso a chamada falhe.

**Atualizar a interface a partir de outra thread.** O loop de flashes roda em uma thread separada, mas mexer na interface diretamente de outra thread causa travamentos e erros. A solução é nunca atualizar a tela diretamente do loop, e sim agendar a atualização de volta na thread principal da interface. Isso mantém tudo estável.

**Banco de dados acessado por várias threads.** Como o loop grava no banco enquanto a interface lê dele, há risco de conflito. A solução usa um bloqueio (lock) em volta de cada operação e configura a conexão para aceitar acesso de múltiplas threads, garantindo que nunca duas operações se atropelem.

**Detectar gravação e reuniões sem bibliotecas pesadas.** Identificar se o Loom ou o Zoom estão rodando poderia exigir bibliotecas complexas. A solução é leve: rodar o comando tasklist do próprio Windows e procurar pelos nomes dos processos, além de checar a tecla Print Screen pela API. Para não pesar, a checagem de processos é feita a cada dez segundos, não a todo instante.

**Manter o consumo de RAM baixo.** A solução está em várias escolhas combinadas: usar tkinter em vez de frameworks pesados, reaproveitar o mesmo elemento de texto a cada flash em vez de criar um novo, e esconder a janela em vez de destruí-la e recriá-la.

**Não travar o desligamento do Windows.** Este é um aprendizado direto dos bugs do software original, que impedia o PC de desligar. A solução é tratar corretamente o evento de fechamento da janela e usar threads do tipo daemon, que encerram junto com o programa sem segurar o sistema.

---

## 12. ESTIMATIVA DE TEMPO {#p1-tempo}

Os tempos abaixo consideram um desenvolvedor de nível intermediário, trabalhando de forma focada. Iniciantes podem levar mais, e quem já domina os temas, menos.

- Janela de overlay transparente e configuração básica: 3 a 4 horas.
- Interface com as abas e personalização visual com preview: 4 a 6 horas.
- Loop de exibição com threading: 2 a 3 horas.
- Banco de dados SQLite e gráficos de estatísticas: 4 a 5 horas.
- Detecção de monitores via ctypes: 2 a 3 horas.
- Pausa automática (processos e Print Screen): 2 a 3 horas.
- Bandeja do sistema e ajustes finais: 2 a 3 horas.

**Resumo:**

- Versão mínima funcional (overlay piscando com mensagens configuráveis): cerca de 1 dia de trabalho.
- Versão completa com todos os recursos: aproximadamente 3 a 5 dias em ritmo de meio período.

A boa notícia é que o projeto é modular. Dá para ter algo funcionando no primeiro dia e ir somando recursos sem precisar reescrever o que já existe.

---

## 13. O QUE VOCÊ VAI GANHAR COM ESTE PROJETO {#p1-ganhos}

Mais do que um aplicativo pronto, este projeto entrega um conjunto de habilidades técnicas que se transferem para muitos outros trabalhos:

**Desenvolvimento de aplicativos desktop.** Você aprende a construir interfaces gráficas completas, com abas, controles, diálogos e atualização em tempo real, algo bem diferente do desenvolvimento web.

**Concorrência e threads.** O loop em segundo plano ensina na prática como rodar tarefas em paralelo sem travar a interface, e como fazer threads se comunicarem com segurança. É um dos conceitos mais valorizados e que mais assusta iniciantes.

**Integração com a API do Windows.** A detecção de monitores e a captura de teclas via ctypes abrem a porta para programar em baixo nível, conversando diretamente com o sistema operacional. Pouca gente domina isso.

**Banco de dados embutido.** O uso do SQLite ensina a persistir e consultar dados localmente, com atenção à concorrência, um padrão presente em incontáveis aplicativos.

**Visualização de dados do zero.** Construir gráficos de barras e de área desenhando no Canvas, sem bibliotecas como matplotlib, ensina a lógica por trás da visualização e dá total controle sobre o resultado.

**Empacotamento e distribuição.** Gerar um executável com PyInstaller fecha o ciclo, ensinando a transformar código em um produto que qualquer pessoa instala e usa.

**Arquitetura de software.** Organizar tudo isso em classes com responsabilidades claras é uma aula de design de código limpo e escalável.

E, claro, uma peça de portfólio memorável: um software desktop real, com recursos que impressionam, muito mais marcante que mais um projeto genérico de cadastro.

---

## 14. COMECE COM CONFIANÇA {#p1-comece}

A maior armadilha de um projeto com tantos recursos é achar que precisa construir tudo de uma vez. Não precisa. O Subliminal Pro é modular por natureza, e o caminho mais inteligente é começar pequeno e ver funcionando rápido.

**Seu primeiro passo.** Comece pela janela de overlay. Em poucas dezenas de linhas você consegue fazer uma mensagem piscar na tela. Esse primeiro momento, ver o texto aparecer e sumir sozinho, é o que prova que a ideia funciona e dá combustível para continuar.

**Depois, uma camada por vez.** Com o overlay pronto, adicione a interface de configuração. Depois o loop automático. Depois as estatísticas. Cada peça nova se encaixa na anterior sem quebrar o que já existe. Você nunca fica travado diante de um projeto gigante, apenas resolve um pequeno desafio de cada vez.

**Existem duas versões de referência.** Há uma versão básica, leve, com o essencial funcionando, e a versão Pro completa. Você pode começar pela básica para entender a fundação e evoluir para a Pro conforme ganha confiança, ou usar a Pro como mapa do destino final.

O projeto toca em temas avançados, é verdade, mas nenhum deles precisa ser dominado antes de começar. Você aprende construindo. Cada desafio técnico vira uma habilidade nova, e ao final você terá não só um software funcionando, mas um salto real de nível como desenvolvedor.

Comece pelo overlay. O resto vem.
