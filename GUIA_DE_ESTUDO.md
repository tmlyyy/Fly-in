# Guia de estudo — Fly-in, thamoliv

Este guia explica a implementação desta pasta a partir do subject
`fly-in.subject.pdf`, versão 2.0, e dos mapas de `maps.tar.gz`.
O README está em inglês porque o subject exige; este material de estudo
está em português. Os links para o código permitem conferir as explicações.
O PDF e o arquivo compactado originais são materiais de referência locais;
o Git pessoal contém o código, o guia e os mapas já extraídos.

## Comece por aqui: modo gráfico e leitura do código

O subject VII.1 permite explicitamente uma interface gráfica que mostre
a rede e a posição dos drones. Não é obrigatório usar apenas o terminal.
Para abrir a visualização desta implementação:

```sh
make run ARGS="--gui"
make run MAP=maps/medium/02_circular_loop.txt ARGS="--gui"
```

O navegador mostra os drones por turno. Use **Reproduzir/Pausar**, **Anterior**,
**Próximo**, **Reiniciar** ou a barra de turnos. O zoom e as barras de
rolagem ajudam nos mapas grandes. O número dentro de cada zona informa
quantos drones estão nela; os IDs aparecem abaixo. Passe o mouse para
conferir a lista completa quando houver muitos drones.

Uma zona restrita tem borda tracejada. Durante a primeira metade da
travessia, o drone aparece em um círculo laranja no meio da conexão.
No turno seguinte ele aparece na zona de destino. Zonas prioritárias
têm estrela e zonas bloqueadas têm um X.

A página é **offline**. Não existe servidor nem instalação de uma
biblioteca gráfica. `make run ARGS="--gui"` salva `build/fly-in.html` e pede ao
navegador padrão para abrir esse arquivo. Você também pode abrir o HTML
manualmente ou gerar sem abrir:

```sh
python3 fly_in.py maps/easy/01_linear_path.txt --html build/fly-in.html
```

GUI significa *Graphical User Interface*, ou interface gráfica do usuário.
`--gui` é uma opção do programa para escolher a visualização no navegador.
O subject permite essa visualização, mas não exige uma regra `make gui`.
Por isso, o Makefile desta pasta tem apenas as cinco regras obrigatórias:
`install`, `run`, `debug`, `clean` e `lint`. Você usa a mesma regra `run`
nos dois modos: sem argumentos para o terminal, ou com `ARGS="--gui"`
para o navegador.

Para manter o código compreensível, a visualização usa uma ideia direta:

```text
Python lê o mapa e planeja os movimentos.
Simulation reproduz os turnos.
GraphicalView desenha um SVG para cada estado.
viewer.html mostra um desses desenhos por vez.
```

SVG é um desenho descrito por texto: `<circle>` faz um círculo, `<line>`
faz uma linha e `<text>` escreve um rótulo. O pequeno bloco de JavaScript
no final do HTML só troca o quadro visível, agenda a reprodução com um
temporizador e ajusta o zoom. Nenhum cálculo de rota foi levado para ele.
Essa escolha simplifica a leitura, mas guarda todos os desenhos no arquivo;
simulações muito grandes geram HTML maior.

Estude os arquivos nesta ordem, sem tentar entender tudo de uma vez:

| Arquivo | O que procurar primeiro |
| --- | --- |
| `models.py` | Quais dados uma zona, conexão e movimento guardam |
| `parser.py` | Como uma linha do arquivo vira esses objetos |
| `simulation.py` | Como posições mudam e capacidades são conferidas |
| `graphical.py` | Como `_frame`, `_connections` e `_hub` desenham o estado |
| `viewer.html` | Como `show`, `play` e `pause` controlam os quadros |
| `routing.py` | Como as rotas e esperas são planejadas |
| `fly_in.py` | Como a aplicação conecta essas partes |

Os módulos e este guia ficam na raiz do repositório. Os mapas ficam
separados por dificuldade em `maps/easy/`, `maps/medium/`, `maps/hard/`
e `maps/challenger/`. O Makefile usa o mapa linear de `maps/easy/`
por padrão; use `MAP=caminho/do/mapa.txt` para escolher outro.

## 1. O problema que você precisa conseguir explicar

Você recebe um grafo: as zonas são os vértices e as conexões são as
arestas. Há vários drones no mesmo início e todos precisam chegar ao
mesmo fim. As conexões são bidirecionais, mas o custo de atravessá-las
depende da **zona de destino**.

Encontrar um caminho curto para um drone é só parte do problema. Quando
vários drones voam, você também precisa decidir **quem ocupa qual recurso
em cada turno**. Uma boa solução combina escolha de caminho e agendamento.

Exemplo: se uma rota tem três movimentos e há dois drones, você não
precisa esperar o primeiro terminar para lançar o segundo. Pode formar
uma fila que avança simultaneamente e terminar em quatro turnos.

O objetivo é minimizar o instante em que o último drone é entregue.
Esse tempo total é chamado de *makespan*. Não é a soma dos tempos de
viagem de todos os drones, nem o tempo que o computador leva para rodar.

## 2. O que o subject exige e onde isso aparece

| Parte | Exigência | Implementação/verificação |
| --- | --- | --- |
| III.1 | Python 3.10+, flake8, mypy e docstrings | Todos os módulos; `make lint`, com tipagem estrita |
| III.1 | Erros tratados e recursos fechados | `Application`, exceções próprias, arquivos abertos com `with` |
| III.2 | Makefile com install/run/debug/clean/lint | `Makefile` |
| III.3 | Testes locais, .gitignore e ambiente virtual | Testes executados no desenvolvimento; `.gitignore` e `.venv` |
| V | Não usar bibliotecas de grafos | Listas de adjacência e algoritmos próprios |
| V | Projeto completamente orientado a objetos e tipado | Classes de domínio e serviços; mypy estrito |
| VI/VII.4 | Ler sintaxe, comentários, metadados e capacidades | `MapParser` em `parser.py` |
| VII.1 | Distribuir drones, esperar, evitar conflitos e ciclos | `Router` e `Reservations` em `routing.py` |
| VII.2 | Limitar ocupação de zonas e conexões | Reservas no planejamento e conferência em `Simulation` |
| VII.3 | Movimentos simultâneos e restritos de dois turnos | `Leg`, `Transit`, `Simulation` |
| VII.5 | Uma linha por turno no formato D<ID>-destino | `Move.__str__` e `Application.run` |
| VII.1/VI | Representação visual e cores dos metadados | `TerminalView`, `GraphicalView` e `viewer.html` |
| VII.6 | Medir validade separadamente da otimização | Validação em cada execução; contagem com `--stats` |
| VIII | README em inglês, crédito, instruções e recursos | `README.md` |
| IX | Bônus: desafio em 43 turnos | Benchmark do Challenger |
| X | Arquivos entregáveis na raiz e defesa do código | Módulos e documentação na raiz |

O subject pede **flake8 para Python**, e não a Norminette de C. Não há
nesse PDF limite de 25 linhas por função, quatro parâmetros ou proibição
de `for`. Não transplante regras de outros projetos sem fundamento no
material desta pasta.

Além do subject, esta revisão considera a régua fornecida no arquivo
`Intra Projects Fly-in Edit.pdf`. O PDF é uma referência local, ignorada
pelo Git para não entrar na entrega. As seções 21 e 22 deste guia
relacionam os critérios com a implementação e explicam o live coding.
Correção e otimização são critérios separados: uma contagem acima do
ótimo não torna, por si só, a simulação incorreta.

## 3. O que se pretende aprender

O subject não fornece uma lista formal de objetivos pedagógicos.
Os objetivos abaixo são uma interpretação das atividades que ele exige:

- **Modelagem:** transformar um enunciado em objetos, estados e invariantes.
- **Grafos:** representar conectividade, ciclos, becos sem saída e gargalos.
- **Algoritmos:** compreender Dijkstra, A*, heurísticas e limites de busca.
- **Planejamento:** conciliar rotas com recursos limitados ao longo do tempo.
- **Simultaneidade:** decidir o próximo estado sem depender da ordem dos IDs.
- **Engenharia:** separar parser, modelo, planejamento, validação e interface.
- **Qualidade:** tratar erros, verificar tipos, seguir estilo e testar limites.
- **Análise:** distinguir execução válida, boa otimização e prova de ótimo.
- **Comunicação:** explicar escolhas, limitações e alterações na avaliação.

O ponto central é desenvolver a capacidade de justificar a solução.
Conseguir executar `make run` não demonstra sozinho esse aprendizado.

## 4. Como executar e observar

Na raiz desta pasta:

```sh
make install
make run
make run ARGS="--gui"
make run MAP=maps/medium/02_circular_loop.txt ARGS="--visual always --color always --stats"
make lint
make debug
make clean
```

`make install` cria um ambiente virtual e instala flake8/mypy. O programa
em si usa somente a biblioteca padrão, então também pode ser executado
com `python3 fly_in.py caminho/do/mapa.txt` sem instalar pacotes.

Neste workspace, a rede para o pip estava indisponível e as versões
exigidas das ferramentas já estavam instaladas no sistema. Por isso a
instalação foi verificada com
`make install VENV_FLAGS=--system-site-packages`, que reaproveita essas
ferramentas. Sem essa opção, o ambiente é isolado e o pip precisa de
acesso aos pacotes ou de um espelho local configurado.

Os programas de teste e de empacotamento foram retirados desta pasta de
entrega. O subject informa que os testes locais não são entregues nem
avaliados. Para conferir um mapa, execute
`make run MAP=maps/easy/01_linear_path.txt ARGS="--stats"`: a aplicação valida a
simulação antes de imprimir e informa a quantidade de turnos.

Observe três canais diferentes:

| Canal | Conteúdo |
| --- | --- |
| stdout | Somente movimentos, uma linha por turno |
| stderr | Visualização, estatísticas e mensagens de erro |
| código de saída | Sucesso/falha para o shell e outros programas |

O terminal normalmente mostra stdout e stderr juntos. Eles continuam
sendo canais diferentes. Para salvar só os movimentos:

```sh
python3 fly_in.py maps/easy/01_linear_path.txt --visual never > /tmp/fly-in-saida.txt
python3 fly_in.py maps/easy/01_linear_path.txt --check /tmp/fly-in-saida.txt
```

No depurador:

```sh
make debug
```

Comandos úteis de `pdb`: `b routing.py:100` cria um breakpoint;
`n` avança uma linha; `s` entra na chamada; `p nome` mostra um valor;
`c` continua; `q` sai. Ajuste o número do breakpoint ao código que quer
estudar. Para investigar uma busca, examine `time`, `name`, `queue`,
`penalties` e `previous` dentro de `Router._path`.

## 5. O formato de entrada

```text
nb_drones: 2
start_hub: s 0 0 [color=green]
hub: r 1 0 [zone=restricted max_drones=1 color=red]
end_hub: e 2 0 [color=yellow]
connection: s-r
connection: r-e
```

A primeira declaração significativa deve ser `nb_drones`. Comentários
iniciados por `#` e linhas vazias são ignorados; isso é necessário porque
os próprios mapas fornecidos começam com comentários.

As coordenadas são inteiros, inclusive negativos. Não representam custo
de viagem: `s` em `(0, 0)` e `e` em `(1000, 1000)` ainda podem estar
ligados por um movimento de um turno. Apenas a conectividade e o tipo
da zona determinam a duração.

Sem metadados, uma zona é `normal`, não tem cor declarada e possui
capacidade 1; uma conexão tem capacidade 1. O início e o fim não têm
limite de ocupação, mesmo que haja `max_drones` declarado. Capacidades
ainda precisam obedecer à sintaxe de inteiro positivo.

Os metadados podem estar em qualquer ordem. Tipos válidos são `normal`,
`restricted`, `priority` e `blocked`. Cores são palavras livres: `rainbow`
não é erro por não fazer parte de uma lista de cores conhecidas.

Nomes de zonas não podem ter espaço nem hífen. O hífen separa os dois
extremos de uma conexão. `a-b` e `b-a` representam a mesma conexão; a
segunda declaração é duplicada. Os extremos precisam existir antes de
a conexão ser declarada.

O parser também rejeita chaves desconhecidas ou repetidas nos metadados,
colchetes malformados e declarações desconhecidas. Essas verificações
impedem que erros de digitação sejam silenciosamente ignorados.

Diferença essencial:

- `connection: s-inexistente` é erro de parsing: há referência inválida.
- Início e fim declarados, mas sem caminho entre eles, formam um mapa
  sintaticamente válido e **sem solução**. O roteador detecta isso.

## 6. Como os objetos representam o problema

Leia [models.py](models.py) antes dos algoritmos.

| Objeto | Responsabilidade |
| --- | --- |
| `ZoneType` | Valores possíveis para acessibilidade e duração de entrada |
| `Hub` | Nome, posição, tipo, cor e capacidade de uma zona |
| `Connection` | Dois extremos, capacidade e nome declarado da ligação |
| `Network` | Frota, zonas, conexões e listas de vizinhos |
| `Leg` | Uma transição planejada com partida e chegada; também representa espera |
| `Move` | Um token de movimento de um drone em um turno |
| `Transit` | Drone em voo que deve chegar à zona restrita no próximo turno |

`@dataclass` gera inicialização e comparação a partir dos campos.
`frozen=True` evita alterações acidentais nos objetos que representam
dados fixos. `Network` constrói as duas direções de cada conexão.

Uma lista de adjacência guarda, para cada nome de zona, os pares
`(vizinho, conexão)`. Assim, procurar saídas de uma zona custa proporcional
ao seu número de vizinhos. Uma matriz completa gastaria `O(V²)` posições
mesmo quando quase todas as zonas não estão conectadas entre si.

Uma conexão tem duas representações úteis:

- `name`: preserva a ordem do arquivo, como `telhado-base`, para a saída.
- `key`: usa os extremos em ordem estável, como `('base', 'telhado')`,
  para compartilhar a capacidade entre os dois sentidos.

A solução é orientada a objetos porque cada parte mantém estado e
comportamento da sua responsabilidade. Não depende de estado global
mutável para controlar a simulação. O bloco `if __name__ == '__main__'`
apenas instancia a aplicação.

## 7. Dijkstra reverso: calcular o que falta até o fim

Leia `Router._distances` em [routing.py](routing.py).

O algoritmo calcula uma vez `distances[zona]`, o menor tempo de viagem
daquela zona até o fim **sem considerar os outros drones**.

Por que não usar somente BFS? BFS minimiza a quantidade de arestas quando
todas custam o mesmo. Aqui, uma entrada restrita custa 2 e uma entrada
normal custa 1. Duas rotas com três arestas podem ter durações diferentes.

Dijkstra funciona com esses custos positivos. A fila de prioridade é um
heap de `heapq`, que sempre retira a menor distância conhecida.

Apesar de a conexão ser bidirecional, os custos direcionais podem mudar:

```text
a normal ---- r restricted
a -> r: 2 turnos
r -> a: 1 turno
```

Na busca reversa, se estamos em `r` examinando seu predecessor `a`,
somamos o custo de **entrar em r**, pois o movimento real é `a -> r`.
Somar o custo de `a` seria um erro.

Pseudocódigo:

```text
dist[fim] = 0
enquanto houver item no heap:
    retirar o item de menor distância
    ignorar entradas antigas do heap
    para cada predecessor acessível:
        candidato = dist[atual] + custo_de_entrar(atual)
        se candidato melhorar dist[predecessor]:
            atualizar distância e inserir no heap
```

Zonas bloqueadas não são incluídas. Se o início não for alcançável nessa
busca, não existe caminho permitido até o fim. A aplicação reporta o
mapa sem solução sem tentar simular indefinidamente.

## 8. Por que buscar no espaço e no tempo

Uma rota estática como `s -> a -> e` não diz se `a` estará ocupada no
turno da chegada. A busca usa estados `(nome_da_zona, instante)`.
Estar em `a` no instante 2 e estar em `a` no instante 5 são estados
diferentes: as reservas existentes podem ser diferentes.

O instante 0 é a posição inicial. Uma `Leg` de partida 0 e chegada 1
gera movimento na primeira linha de saída.

| Transição | Estado de origem | Estado de chegada |
| --- | --- | --- |
| Esperar | `(a, t)` | `(a, t + 1)` |
| Entrar em normal/priority | `(a, t)` | `(b, t + 1)` |
| Entrar em restricted | `(a, t)` | `(r, t + 2)` |
| Entrar em blocked | Não há transição | Não há estado sucessor |

O estado intermediário de conexão não precisa participar da busca como
um vértice adicional: a transição restrita conhece sua duração, reserva
o recurso correspondente e gera os dois movimentos de saída. Durante
a reprodução, `Transit` representa explicitamente esse estado.

## 9. A*: entregar o próximo drone o mais cedo possível

Leia `Router._path`, `_successors` e `_reconstruct`.

A* ordena estados por:

```text
f = tempo já decorrido + estimativa mínima de tempo restante
f = t + distances[zona]
```

Como as distâncias ignoram congestionamento, elas nunca superestimam
o tempo que falta quando há reservas. Essa é a ideia de uma heurística
**admissível**. O valor também é consistente nas transições: mover ou
esperar não torna possível reduzir o custo restante além do tempo gasto.

Entre candidatos de mesmo `f`, a implementação usa uma penalidade de
desempate: cada entrada em zona que não é `priority` acrescenta 1;
entradas em `priority` e esperas acrescentam 0. Quando o estado de fim
é retirado do heap, isso favorece menos entradas em zonas não prioritárias
entre entregas igualmente cedo. Não há recompensa negativa nem mudança
do custo físico. Uma rota prioritária mais lenta não ganha de uma entrega
que pode terminar antes.

`penalties[(zona, tempo)]` guarda a melhor penalidade para esse estado.
Não se confunde com duração de viagem. Um candidato pior para o mesmo
estado é descartado. Itens antigos do heap também são ignorados.

`previous` guarda a `Leg` que levou a cada estado. Ao alcançar o fim,
`_reconstruct` percorre esses predecessores de trás para frente e inverte
a lista. Isso evita copiar uma rota inteira a cada expansão.

### O limite da busca

O horizonte é:

```text
H = última chegada já reservada + menor duração do início até o fim
```

Esse limite tem uma justificativa: o novo drone pode ficar no início,
que comporta a frota inteira, até todos os anteriores serem entregues.
Depois disso, segue um caminho mínimo sem interferência. Portanto,
existe uma opção viável até `H` para qualquer mapa acessível.

Os estados avançam estritamente no tempo, e só entram no heap quando
ainda podem chegar até `H`. Mesmo que o grafo tenha ciclos, a busca tem
um espaço finito. O programa não usa um corte arbitrário como “no máximo
100 drones” ou “desistir depois de 1.000 turnos”. Memória e tempo da
máquina continuam sendo limites físicos.

## 10. Reservas: a parte que coordena os drones

`Reservations` mantém dois mapas esparsos:

```text
zones[(nome, instante)] = quantidade reservada nessa zona
links[((extremo1, extremo2), turno)] = novas travessias nesse turno
```

A busca usa `.get(..., 0)` para consultar. Isso evita criar entradas de
valor zero só por examinar uma possibilidade. Ao confirmar o caminho,
`reserve` incrementa as reservas realmente usadas.

Para entrar em uma zona normal, o roteador exige vaga no instante de
chegada e capacidade na conexão no turno do movimento. Para esperar,
exige vaga na mesma zona no próximo instante. Para entrar em uma zona
restrita, exige capacidade na conexão no próximo turno e vaga na zona
dois instantes à frente.

Essa reserva de chegada é o que impede lançar um drone para uma zona
restrita esperando descobrir mais tarde se haverá vaga.

### Linha do tempo de uma entrada restrita

Considere `s -> r -> e`, com `r` restrita e tudo de capacidade 1:

| Turno | Drone 1 | Drone 2 | stdout |
| ---: | --- | --- | --- |
| 0 | Em s | Em s | Ainda não há linha de movimentos |
| 1 | Na conexão s-r | Esperando em s | `D1-s-r` |
| 2 | Chega em r | Inicia voo na s-r | `D1-r D2-s-r` |
| 3 | Chega em e | Chega em r | `D1-e D2-r` |
| 4 | Entregue | Chega em e | `D2-e` |

A primeira travessia parte do instante 0, ocupa a conexão no turno 1
e chega no turno 2. A conexão pode receber outro drone **no turno 2**,
porque o anterior sai dela naquele mesmo turno.

Cobrar a capacidade novamente na chegada impediria esse encadeamento
e contrariaria o exemplo explícito do subject VII.3. Para movimentos
normais, a capacidade da conexão também é cobrada no turno de movimento.
Sentidos opostos usam o mesmo contador.

### Por que não há colisões nas reservas

Um argumento por indução ajuda a defender o código:

1. Sem drones planejados, não há reserva nem conflito.
2. Suponha que as rotas anteriores sejam válidas.
3. A nova rota só usa zonas/instantes e conexões/turnos com capacidade
   restante. Todas as chegadas e esperas são registradas.
4. Logo, acrescentar essa rota não ultrapassa nenhuma capacidade.
5. Repetindo o processo, o conjunto de rotas mantém essas propriedades.

Esse argumento depende de a implementação registrar corretamente os
recursos. Por isso existe também um simulador independente: a prova da
ideia não elimina a possibilidade de erro de programação.

## 11. Simular simultaneamente não é mover um ID de cada vez

Leia [simulation.py](simulation.py).

Se você alterar as posições imediatamente ao ler cada movimento, o
resultado pode depender da ordem dos tokens. Isso seria incorreto.

Exemplo: D1 está em `a`, D2 está no início. No mesmo turno, D1 vai para
`b` e D2 entra em `a`. A capacidade de `a` é 1. A operação é válida
porque a saída de D1 libera a vaga para a chegada de D2.

`Simulation` faz o seguinte:

1. Copia as posições anteriores para um estado candidato.
2. Interpreta cada movimento usando **as posições do início do turno**.
3. Rejeita IDs inválidos, repetidos ou já entregues.
4. Exige que todo drone em `Transit` faça a chegada obrigatória.
5. Conta a ocupação das zonas no estado candidato completo.
6. Conta as novas travessias em cada conexão, compartilhando sentidos.
7. Só confirma o estado quando tudo passa.

Uma falha deixa turno, posições e entregas intactos. Esse comportamento
é chamado de atualização atômica ou transacional.

O simulador não consulta `Reservations` nem as distâncias de Dijkstra.
Ele verifica os movimentos como um consumidor externo da saída.
Isso reduz o risco de planejamento e verificação repetirem exatamente
o mesmo erro de agendamento. Os testes manuais de conflito complementam
essa separação, pois nenhum verificador é infalível.

Antes de imprimir qualquer movimento, a aplicação reproduz e valida
**o plano inteiro**. Assim, uma falha de validação não deixa uma saída
parcial com aparência de simulação concluída.

## 12. Percurso completo no mapa linear

O mapa é `start -> waypoint1 -> waypoint2 -> goal`, com dois drones.
As distâncias até o fim são:

```text
goal: 0
waypoint2: 1
waypoint1: 2
start: 3
```

Para D1, a busca reserva `waypoint1` no instante 1, `waypoint2` no 2 e
`goal` no 3. Cada conexão é usada no respectivo turno de partida.

Para D2, entrar em `waypoint1` no instante 1 não é permitido. A busca
inclui a transição de espera no início e chega em `waypoint1` no 2.
Isso é permitido porque D1 estará em `waypoint2` nesse instante.

Resultado:

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

É possível justificar o ótimo desse mapa: a primeira entrega precisa
de três turnos, e a capacidade 1 da última conexão impede entregar os
dois drones no mesmo turno. Portanto, menos de quatro é impossível.

## 13. Desempenho e limites reais da estratégia

O planejamento é **priorizado**: primeiro fixa D1, depois D2 e assim por
diante. Drones posteriores podem usar outras rotas ou esperar, mas não
replanejam os anteriores.

Cada busca encontra uma chegada mais cedo considerando as reservas já
fixadas. Isso **não prova ótimo global** para o conjunto. Em outro grafo,
mover o primeiro drone por uma rota um pouco mais lenta pode liberar um
recurso importante e antecipar a última entrega. Nosso algoritmo não
explora todas essas revisões conjuntas.

Por que escolher assim? A solução mantém estados simples, considera
todo o grafo acessível, trata capacidades e esperas diretamente, termina
com uma alternativa viável e alcança os alvos dos mapas fornecidos.
Não precisa enumerar todas as combinações de posição da frota.

Uma alternativa conjunta buscaria um estado com a posição de todos
os drones. Mesmo antes de considerar o tempo e os recursos, o número
de combinações pode crescer como `V^D`. Essa abordagem pode ser exata,
mas costuma ficar muito mais cara. Há métodos mais sofisticados de
replanejamento e busca de conflitos; não foram implementados aqui.

### Complexidade

Defina `V` como zonas acessíveis, `E` como conexões, `D` como drones
e `H` como o maior horizonte encontrado.

| Etapa | Tempo aproximado no pior caso |
| --- | --- |
| Parsing e construção do grafo | Linear no tamanho do arquivo, com dicionários em custo esperado constante |
| Dijkstra reverso | `O((V + E) log V)` |
| Busca espaço-tempo de um drone | `O(H (V + E) log(VH))` |
| Todas as buscas | `O(D H (V + E) log(VH))` |
| Validação | `O(DT + K)`, para T turnos e K movimentos impressos |

Em um instante pode haver um estado por zona e transições pelos seus
vizinhos. Multiplicar por `H` dá a dimensão temporal. O heap acrescenta
o fator logarítmico. O desempate por penalidade também é monotônico.

Memória da busca e das reservas tem limite conservador
`O(H(V + E))`, além do armazenamento da saída. O programa guarda o plano
inteiro para poder validá-lo antes de imprimir. Isso troca mais memória
por uma garantia de saída previamente conferida.

`H` não é constante: pode crescer junto com a frota. Portanto, não diga
que planejar mil drones é necessariamente só mil vezes o custo de um,
nem que A* torna qualquer grafo barato. O ganho prático depende da
heurística e da quantidade de estados realmente expandidos.

O que é reaproveitado? Distâncias e grafo são calculados uma vez.
O caminho completo é pesquisado para cada drone, porque as reservas
mudam após cada planejamento. A geometria não é usada como heurística,
pois o subject não relaciona distância cartesiana com duração de voo.

## 14. Resultados dos mapas fornecidos

| Mapa | Ótimo do subject | Resultado validado |
| --- | ---: | ---: |
| Linear path | 4 | 4 |
| Simple fork | 4 | 4 |
| Basic capacity | 4 | 4 |
| Dead end trap | 8 | 8 |
| Circular loop | 10 | 10 |
| Priority puzzle | 6 | 6 |
| Maze nightmare | 13 | 13 |
| Capacity hell | 16 | 16 |
| Ultimate challenge | 26 | 26 |
| The Impossible Dream | 43 | 43 |

Para conferir cada resultado, use `make run MAP=maps/medium/02_circular_loop.txt
ARGS="--stats"` em uma única linha. A aplicação valida os movimentos e
informa a contagem de turnos. Os números da tabela foram medidos nesta
implementação; a coluna de ótimo vem do PDF, não de uma prova de ótimo
produzida pelo programa.

O README dos mapas fala em um recorde antigo de 45 turnos no Challenger.
O PDF versão 2.0 estabelece 43 e explica o limite: a primeira entrega
precisa de 19 turnos, e um gargalo de capacidade 1 exige mais 24 turnos
para os outros 24 drones. Alcançar `19 + 24 = 43` atinge esse limite.
O bônus só é considerado quando o obrigatório está completo.

## 15. O que os testes verificam

Os testes executados no desenvolvimento usaram `unittest`, sem dependência
adicional. Seus arquivos não fazem parte desta entrega. Eles incluíram:

- Gramática válida, Unicode, comentários e metadados em outra ordem.
- Frota/capacidades inválidas, coordenadas inválidas, tipo inexistente,
  duplicatas, referência antecipada e colchetes incorretos.
- Grafos desconectados e caminhos interrompidos por zonas bloqueadas.
- Pipeline normal e liberação de zona no mesmo turno.
- Trânsito restrito obrigatório, chegada antecipada inválida e conexão
  reutilizada no turno da chegada do drone anterior.
- Conexão compartilhada por sentidos opostos.
- Diferença entre capacidade de zona e capacidade de conexão.
- Falhas atômicas: uma tentativa inválida não altera o estado.
- Desempate por prioridade e conexão declarada em sentido inverso.
- Frota de mil drones e 150 grafos conectados com semente fixa 42.
- stdout exato, leitura e reprodução da saída, cores e erros sem traceback.
- Os dez alvos do subject, com reprodução independente de cada resultado.

Os grafos gerados variam tipos, capacidades, ciclos, caminhos alternativos
e quantidade de drones. São testes de validade, não uma certificação de
ótimo global. Usar semente fixa permite reproduzir os mesmos casos.

`make lint` executa as verificações obrigatórias, com todas as flags
de mypy pedidas no PDF e o modo estrito habilitado em `mypy.ini`.
Nenhuma regra de estilo foi desativada. O uso de um único
worker do flake8 permite rodar também em ambientes que bloqueiam os
sockets usados por pools de processos.

O mypy verifica compatibilidade de tipos mirando Python 3.10. A execução
disponível neste ambiente usa Python 3.14.4. Isso deve ser distinguido
de uma execução real em 3.10, que não estava instalado aqui.

## 16. Erros, tipos e documentação

`FlyInError` agrupa falhas previstas de domínio. `ParseError` acrescenta
a linha do mapa. `SimulationError` comunica movimentos inválidos.
A aplicação também trata falhas de arquivo e codificação. Arquivos
usam `with`, que fecha o recurso mesmo quando há exceção.

Não há `except Exception: pass`: isso esconderia defeitos e poderia
produzir uma simulação incompleta como se tivesse dado certo. São
tratadas as falhas previstas, preservando mensagens úteis.

Anotações como `dict[int, str | Transit]` expressam que um drone ainda
ativo pode estar em uma zona ou em trânsito. `isinstance` permite ao
mypy e ao leitor distinguir os casos. Uma `Leg` pode ter
`Connection | None`: `None` representa uma espera sem travessia.

Tipagem estática não confere se a capacidade 1 foi respeitada no turno 5.
Esse é um invariante de execução, verificado pelas reservas e pelo
simulador. Flake8 também não prova correção algorítmica: confere estilo
e detecta algumas classes de erro. Cada ferramenta cobre uma parte.

Docstrings explicam a finalidade de classes e métodos. Comentários
explicam decisões específicas, como validar o plano inteiro antes da
saída. O material de estudo fornece a explicação longa sem transformar
cada linha de Python em um comentário repetitivo.

## 17. Roteiro de estudo sugerido

1. **Entenda as regras:** leia VI e VII do subject e refaça à mão os mapas
   linear e restrito deste guia. Explique cada linha sem olhar o código.
2. **Leia os modelos:** desenhe um `Network` pequeno e sua lista de adjacência.
   Distinga `Move`, `Leg` e `Transit` com exemplos.
3. **Estude o parser:** altere uma entrada por vez e preveja linha e causa
   do erro antes de executar.
4. **Domine os custos:** calcule manualmente as distâncias reversas de um
   grafo com uma zona restrita. Compare BFS e Dijkstra nesse grafo.
5. **Siga uma busca:** no depurador, observe o heap, a prioridade e os
   predecessores de D1 e D2 do mapa linear.
6. **Inspecione reservas:** anote quais pares `(recurso, turno)` foram
   usados, sobretudo na entrada restrita.
7. **Estude o validador:** inverta a ordem dos tokens de um turno válido.
   Explique por que o estado final permanece o mesmo.
8. **Meça e questione:** rode o benchmark e explique a diferença entre
   acertar os alvos fornecidos e resolver qualquer grafo otimamente.
9. **Pratique mudanças:** faça um exercício abaixo, rode lint/testes e
   peça que um colega revise sua explicação e o comportamento.

Não existe duração obrigatória para essas etapas. Avance quando conseguir
explicar o trecho e prever o efeito de uma pequena mudança.

## 18. Perguntas de defesa com respostas para conferir

**Por que o custo é associado ao destino?**
Porque entrar em uma zona restrita custa dois turnos, enquanto sair dela
para uma zona normal custa um. A ligação não tem um peso simétrico fixo.

**Por que BFS não basta?**
Os pesos não são todos iguais. BFS minimiza arestas, não necessariamente
tempo total. Depois, ainda seria preciso tratar reservas e esperas.

**Por que não usar a distância entre as coordenadas no A*?**
O mapa não garante relação entre geometria e tempo. Essa distância
poderia superestimar o custo e invalidar a justificativa da heurística.

**O que significa uma heurística admissível aqui?**
Ela não promete um tempo menor que o já decorrido; estima o restante
sem ultrapassar o custo real mínimo restante. As distâncias sem outros
drones são um limite inferior quando se acrescentam congestionamentos.

**Como um drone sabe que poderá sair da conexão restrita?**
A chegada na zona é reservada ao planejar a transição, dois instantes
à frente. Depois, o simulador exige essa chegada no próximo turno.

**Drones podem trocar de zona no mesmo turno?**
Só se cada entrada, ocupação final e uso de conexão respeitar as regras.
Duas travessias opostas da mesma ligação de capacidade 1 são inválidas,
mesmo que as zonas finais caibam. Com capacidade 2, esse conflito
específico deixa de existir; custos de destino ainda precisam ser atendidos.

**O início e o fim são realmente ilimitados?**
O domínio usa a frota total como capacidade efetiva. Não pode haver
mais drones que esse total. Entregues são removidos da simulação.

**Por que a busca termina mesmo com ciclos?**
Cada transição avança o tempo e existe um horizonte finito justificado.
Estados repetidos só melhoram se a penalidade for menor.

**A ordem de planejamento dos drones afeta a qualidade?**
Sim. As reservas dos anteriores ficam fixas. Ela não muda o significado
de movimentos simultâneos, que o simulador verifica separadamente.

**O algoritmo é globalmente ótimo?**
Não há essa garantia geral. Ele atingiu os dez alvos fornecidos e garante
uma alternativa de entrega para os drones em mapas acessíveis, dentro
dos recursos disponíveis. Não revisa decisões anteriores em conjunto.

**Atingir 43 turnos basta para aprovar?**
Não. O bônus depende do obrigatório e a avaliação também exige tipos,
estilo, orientação a objetos, correção e entendimento do autor.

**Por que validar antes de imprimir?**
Para não entregar um prefixo de movimentos que só mais tarde se revela
inválido. A contrapartida é manter o plano inteiro em memória.

## 19. Exercícios práticos de alteração

Faça em uma cópia ou branch de estudo. Após cada alteração, rode
`make lint` e execute os mapas com `make run MAP=maps/medium/02_circular_loop.txt
ARGS="--stats"` em uma única linha se a lógica de rotas mudar.

1. **Cor desconhecida:** mude `color=blue` para `color=oceano`. Preveja
   se o parser deve aceitar e o que a visualização mostrará.
2. **Gargalo de zona:** em `maps/easy/03_basic_capacity.txt`, reduza a capacidade
   de `bottleneck` de 2 para 1. Calcule por que a última entrega passa
   de 4 para 6 turnos, sem mudar a capacidade das conexões.
3. **Nova estatística:** acrescente ao relatório o número de tokens
   impressos. É `sum(len(turno) for turno in turns)`. Não conte uma
   espera omitida como movimento e lembre que uma entrada restrita
   imprime dois tokens em turnos diferentes.
4. **Outro desempate:** entre zonas da mesma prioridade e mesma duração,
   prefira maior capacidade. Identifique o ponto da fila/penalidade a
   alterar sem dar custo físico negativo ou sacrificar uma chegada anterior.
5. **Erro explicativo:** melhore a mensagem de excesso de capacidade
   para mostrar ocupação e limite. Altere o validador e seu teste, sem
   modificar o algoritmo de planejamento.
6. **Mapa sem solução:** crie um mapa em que a única passagem seja
   bloqueada. Explique por que o parser aceita e o roteador rejeita.
7. **Independência de ordem:** em uma saída válida, inverta os tokens
   de cada linha. Reproduza e confira o mesmo resultado final.
8. **Contraexemplo de qualidade:** tente desenhar duas rotas em que a
   primeira entrega mais rápida use um gargalo importante para várias
   entregas seguintes. Compare manualmente com uma decisão que atrase
   o primeiro drone e melhore o fim da frota. O exercício é investigar
   a limitação do planejamento priorizado, não alterar os benchmarks.

## 20. Antes da entrega e da revisão por pares

O capítulo X diz que apenas o conteúdo do repositório será avaliado.
Os arquivos foram criados no workspace; isso não é um commit nem um
envio para a 42. Confira a inclusão dos módulos, configurações,
`requirements.txt`, Makefile, README e mapas necessários no seu Git.
Os diretórios `.venv`, caches e o teste local estão ignorados.

O crédito do README usa o login `thamoliv`, informado nesta conversa.
Rode os comandos na máquina de entrega, com a versão de Python que
será usada na avaliação.

O subject exige revisão crítica e recomenda aprendizagem entre pares.
A implementação e as verificações automáticas já foram realizadas;
a compreensão pessoal e a revisão com colegas precisam acontecer com
você. Tente explicar uma simulação restrita, a distância reversa, o
horizonte e a limitação de ótimo sem consultar este guia.

## 21. Conferência com a régua de avaliação

A referência desta revisão é o PDF `Intra Projects Fly-in Edit.pdf`,
com sete páginas. Os testes desta conferência ficam fora da pasta de
entrega. A tabela distingue comportamentos que podemos verificar por
execução de itens que dependem da sua presença e explicação na defesa.

| Critério da régua | O que foi conferido | Situação |
| --- | --- | --- |
| Presença e repositório oficial | A defesa exige a presença do aluno e o repositório correto | Conferência humana na avaliação |
| Arquivos de entrega | Código, Makefile, configurações, mapas e documentação; PDF local ignorado pelo Git | Preparado; confira o conteúdo do Git oficial |
| README | Primeira linha em itálico com `thamoliv`, inglês, Description, Instructions, Resources, Algorithm explanation, visualização e exemplo | Conferido |
| Orientação a objetos | Modelos e serviços em classes; responsabilidades de parsing, roteamento, simulação e apresentação separadas | Conferido no código |
| Tipagem e estilo | `make lint`, `flake8 .` e `mypy .`; modo estrito habilitado | Passaram |
| Grafo próprio | Lista de adjacência; Dijkstra e A* implementados sem bibliotecas de grafos | Conferido no código |
| Makefile | `install`, `run`, `debug`, `clean`, `lint` | Regras verificadas |
| Parsing válido | Frota, três tipos de declaração de zona, conexões, metadados, defaults, comentários e linhas vazias | Testado |
| Parsing inválido | Formatos, tipos e capacidades inválidos; terminais ausentes/repetidos; duplicatas e referências inexistentes | Testado com mensagens de erro |
| Ocupação e duração | Capacidades, início/fim ilimitados, normal e priority de um turno, restricted de dois, blocked inacessível | Testado |
| Capacidade de conexão | Capacidade compartilhada por sentidos opostos; liberação no turno da chegada restrita | Testado |
| Visualização | Cores, IDs, ocupação, trânsito restrito e entregas no terminal/HTML | Verificado |
| Casos simples e formato | Um drone, vários caminhos, uma linha por turno, IDs únicos e esperas omitidas | Testado |
| Encerramento | Todos entregues; nenhuma movimentação posterior de um drone entregue | Testado |
| Rotas e conflitos | Gargalos, ciclos, esperas e reserva antecipada da chegada restrita | Testado |
| Explicação do algoritmo | Complexidade, reservas, heurística e limitação de ótimo estão neste guia | Você precisa explicar na defesa |
| Nove mapas obrigatórios | Simulações válidas e contagens iguais aos ótimos da régua | Passaram |
| Casos extremos | Um drone, grafo desconectado, gargalos e capacidades de até `1000000000000` | Testado |
| Live coding | Dados de uso disponíveis; alteração pequena da apresentação praticada em cópia isolada | Preparação pronta; demonstração ao vivo ainda necessária |
| Bônus | Challenger entregue em 43 turnos | Alvo técnico atingido; depende do obrigatório |

O README recebeu o título **Algorithm explanation**, como aparece na
régua. O resumo visual foi separado em `TerminalView._summary`. O
simulador passou a guardar os contadores do último turno válido, sem
alterar as decisões de rota nem o formato dos movimentos.

Na regra `run`, o `@` antes do comando só impede que o Makefile repita
esse comando em stdout. O programa continua sendo executado normalmente.
Isso permite salvar a saída com `make run > arquivo.txt` sem acrescentar
uma linha que não seja um turno da simulação.

### Validade, margem e ótimo são perguntas separadas

| Mapa obrigatório | Ótimo | Limite da régua: +25% | Resultado conferido |
| --- | ---: | ---: | ---: |
| Linear path | 4 | 5 | 4 |
| Simple fork | 4 | 5 | 4 |
| Basic capacity | 4 | 5 | 4 |
| Dead end trap | 8 | 10 | 8 |
| Circular loop | 10 | 13 | 10 |
| Priority puzzle | 6 | 8 | 6 |
| Maze nightmare | 13 | 17 | 13 |
| Capacity hell | 16 | 20 | 16 |
| Ultimate challenge | 26 | 33 | 26 |

O limite é `ceil(1.25 * ótimo)`, isto é, arredondado para cima. Todos
esses mapas passaram pela validação de movimentos antes da comparação
dos turnos. No bônus, o resultado continua sendo 43 turnos.

Para conferir um mapa na sua máquina:

```sh
make run MAP=maps/hard/02_capacity_hell.txt ARGS="--visual never --stats"
```

Flake8/mypy, execução e demonstrações não estabelecem a nota final.
Presença, revisão por pares, compreensão e live coding são avaliados
na defesa. A régua considera apenas o Git oficial da entrega, que deve
ser conferido separadamente do GitHub pessoal. O guia é material de
estudo solicitado para o repositório pessoal; confira com as regras de
submissão quais documentos adicionais incluir no Git oficial.

O ambiente disponível executou Python 3.14.4. A sintaxe e a tipagem
miram Python 3.10, mas esta conferência não equivale a executar o
projeto em um interpretador 3.10 instalado na máquina da avaliação.

## 22. Live coding da régua em um único método

### O que realmente será pedido

A régua pede acrescentar a exibição, **a cada turno**, da capacidade
utilizada de **uma zona** e **uma conexão**. O exemplo é semelhante a:

```text
Zone junction: 2/2 drones, Connection start-junction: 2/2 capacity used
```

Ela permite aproveitar uma flag, um controle visual ou uma linha de log
que combine com a arquitetura existente. O prazo indicado é de até
**10 minutos, incluindo a demonstração**. Você precisa localizar o
parsing e a saída, fazer a alteração e explicar por que ela funciona.

Nesta implementação, basta trabalhar no resumo do terminal. Não é
necessário modificar A*, Dijkstra, reservas, HTML ou o parser.

### Onde estão os dados

| Informação | Local |
| --- | --- |
| Capacidade declarada da zona | `models.py`: `Hub.capacity` |
| Leitura de `max_drones` | `parser.py`: `MapParser._hub` |
| Capacidade declarada da conexão | `models.py`: `Connection.capacity` |
| Leitura de `max_link_capacity` | `parser.py`: `MapParser._connection` |
| Drones na zona após o turno | `simulation.zone_occupancy[nome]` |
| Uso da conexão naquele turno | `simulation.link_usage[edge.key]` |
| Lugar pequeno para mudar a saída | `display.py`: `TerminalView._summary` |

Os dois contadores são `Counter`: uma chave ausente representa zero.
Eles só são atualizados depois que o turno inteiro é validado. Se um
movimento é rejeitado, posições e contadores anteriores permanecem
intactos.

`zone_occupancy` conta drones ativos no estado final do turno. Ela não
conta reservas futuras. `link_usage` conta as travessias iniciadas naquele
turno: movimento normal ou entrada no primeiro turno de um trânsito
restrito. A chegada de um trânsito restrito libera a conexão e não cobra
a capacidade novamente. Os dois sentidos usam a mesma chave.

### A alteração para praticar

Abra `display.py` e encontre `def _summary`. O método atual já mostra
quantos drones foram entregues. Para treinar o pedido da régua, substitua
**somente esse método** pela versão abaixo:

```python
    def _summary(self, simulation: Simulation) -> str:
        """Show deliveries and the capacity of one zone and connection."""
        zone = self.network.hubs["junction"]
        edge = self.network.connections[("junction", "start")]
        zone_used = simulation.zone_occupancy[zone.name]
        link_used = simulation.link_usage[edge.key]
        return (
            f"Delivered: {simulation.delivered}/{self.network.drone_count}"
            f" | Zone {zone.name}: {zone_used}/{zone.capacity} drones"
            f", Connection {edge.name}: "
            f"{link_used}/{edge.capacity} capacity used"
        )
```

As primeiras quatro atribuições escolhem os recursos e leem os números.
As strings seguintes montam a mensagem. O método não muda nenhuma posição,
capacidade ou decisão de rota.

Os nomes foram escolhidos para `maps/easy/02_simple_fork.txt`. A conexão
é declarada como `start-junction`, mas sua chave é `("junction", "start")`
porque os extremos são ordenados alfabeticamente para compartilhar os
dois sentidos. `edge.name` conserva a ordem da declaração para exibição.
Se o avaliador escolher outro mapa, ajuste esses nomes para recursos
que existam nele.

Para esse exercício, escolha uma zona intermediária. Início e fim são
ilimitados: se forem escolhidos, mostre `unlimited` como limite em vez
de usar o valor bruto de `Hub.capacity`. Drones entregues são removidos
das posições ativas; o total entregue continua em `simulation.delivered`.

### Como demonstrar

Depois da pequena alteração, execute:

```sh
make lint
make run MAP=maps/easy/02_simple_fork.txt ARGS="--visual always --color never"
```

`--visual always` é necessário para mostrar o resumo mesmo quando o
terminal não é detectado como interativo. `--color never` facilita ler
e comparar o texto. Não use `--gui` para essa demonstração: essa opção
seleciona a apresentação no navegador e desativa o resumo do terminal.

Os números esperados para os recursos escolhidos são:

| Estado/turno | junction | start-junction | Entregues |
| ---: | ---: | ---: | ---: |
| Inicial, 0 | 0/2 | 0/2 | 0/4 |
| 1 | 2/2 | 2/2 | 0/4 |
| 2 | 2/2 | 2/2 | 0/4 |
| 3 | 0/2 | 0/2 | 2/4 |
| 4 | 0/2 | 0/2 | 4/4 |

O estado 0 é apenas o desenho inicial, antes do primeiro movimento.
Observe que a conexão volta a zero quando não é usada. O contador não
é uma soma acumulada de todos os drones que já passaram por ela.

Para demonstrar que a mudança não quebrou o formato obrigatório:

```sh
make run MAP=maps/easy/02_simple_fork.txt ARGS="--visual always --color never" > /tmp/fly-in-live-output.txt
python3 fly_in.py maps/easy/02_simple_fork.txt --check /tmp/fly-in-live-output.txt --visual never
```

O resumo e os diagnósticos vão para **stderr**; o arquivo recebe somente
os movimentos de **stdout**. A segunda chamada deve confirmar quatro
drones entregues em quatro turnos.

### Roteiro para caber nos dez minutos

1. Mostre `_hub` e `_connection` no parser e os campos de capacidade nos
   modelos. Explique que esses valores já foram lidos corretamente.
2. Abra `_summary` em `display.py` e escolha os nomes presentes no mapa.
3. Leia os dois contadores e acrescente os valores ao texto do resumo.
4. Rode `make lint` e a demonstração com `--visual always`.
5. Explique a saída: ocupação final da zona, uso da conexão no turno,
   limites e separação entre stdout e stderr.

Pratique esse roteiro com um cronômetro e sem consultar o trecho pronto.
A versão do código entregue mantém o resumo original; os contadores
apenas deixam os dados acessíveis. A alteração desta seção foi testada
em uma cópia isolada, inclusive com flake8 e mypy estrito. Ter o exemplo
no guia não substitui implementar e explicar a mudança que o avaliador
solicitar ao vivo.
