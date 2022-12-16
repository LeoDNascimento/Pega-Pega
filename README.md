# 🕹️Pega-Pega - multiplayer game

## Visão Geral
Esse programa é um protótipo de jogo multiplayer de pega pega utilizando a linguagem Python e suas libs de socket + Pygame.  
O objetivo do jogo é o player colidir primeiro com o outro player antes que ele faça o mesmo.
Ganha ao final aquele que fizer mais pontos até o final do turno de 30 segundos.

## Como inicializar
### Requisitos
* Python 3
* Pygame (pip install pygame)

### Inicializar
Obs: Não precisa iniciar na venv presente no código, apenas tendo os pré requisitos e rodando cada código irá funcionar, seja windows ou linux.
```
HOST_IP = socket.gethostbyname(socket.gethostname())
HOST_PORT = 12345
```

1. Iniciar/Rode o código server.py e espere a confirmação que inicializou o server e está "escutando"
2. Iniciar/Rode o código client.py o número de players permitidos (por padrão está 2, mas pode aumentar até 4 alterando a linha 12 do server.py)
3. Todas os players/janelas precisa pressionar o Enter para que possa iniciar o jogo

OBS: não precisa se preocupar com o HOST IP ou alterar isso no client, pois pega automático por causa da linha:
`HOST_IP = socket.gethostbyname(socket.gethostname())` que está tando no server quanto no client.  
O PORT é 12345


## Funcionamento e Protocolo
### Server
O server.py é responsável por toda a lógica e padronização do jogo. Em que ele que possui todas as informações básicas que garantem o funcionamento e variáveis básicas do jogo como:  
```
# Variaveis para  janela do pygame
ROOM_SIZE = 700
PLAYER_SIZE = 140
ROUND_TIME = 30
FPS = 15
TOTAL_PLAYERS = 2
```  

Essas informações são importantes por conta que é um jogo multiplayer e serão abertos mais de 1 client, então precisa garantir que estarão com mesma configuração. Por cotna disso achei melhor ser responsabilidade do server.  
OBS: o server **não possui o pygame**, apenas o client para fazer as interfaces.  

O server será o responsável por reaizar o envio dos estados do jogo e jogadores:
* Coordenadas dos players: aonde cada quadradinho (jogador) está no momento.
* Estado do game: o que está acontecendo no jogo. Se tem alguém jogando, quantos tem, se já começou, se já acabou...

## Funções responsáveis pelo envio de coordenadas dos jogadores: 
### Jogadores entrando e sendo alocados:
A `class Player():` na linha 30 do server.py irá conter tudo sobre as coordenadas iniciais:
```
        self.x = self.starting_x # irá depender de qual player é, mas será uma coordenada x em algum dos cantos da tela
        self.y = self.starting_y # irá depender de qual player é, mas será uma coordenada x em algum dos cantos da tela
        self.dx = 0
        self.dy = 0
        self.coord = (self.x, self.y, self.size, self.size) # Locaização inicial do jogador. Como é inicial será algum dos cantos

        self.is_waiting = True # Como é inicio, o jogador inicia esperando os outros jogadores e não poderá se movimentar
        self.is_ready = False # Ele necessitará apertar Enter na tela para demonstrar que está pronto para jogar
        self.is_playing = False # Estado que idica se o jogo iniciou  
```

JSON ENVIADO AO CLIENT QUANDO HÁ CONEXÃO DE UM PLAYER NOVO:
```
{
"number": 1, 
"size": 140, 
"score": 0, 
"starting_x": 0, 
"starting_y": 0, 
"p_color": [255, 0, 0], 
"s_color": [150, 0, 0], 
"x": 0, "y": 0, "dx": 0, "dy": 0, 
"coord": [0, 0, 140, 140], 
"is_waiting": true, 
"is_ready": false, 
"is_playing": false, 
"status_message": "Aguardando 2 jogadores"
}  
```
Esse procedimento é realizado pela `def connect_players(self):` na linha 91 e a conversão para Json e a transmissão inicial pela `def broadcast(self):" na linha 142.  

O resto é bem básico e pode ser resumido em: o server irá ficar enviando o mesmo Json que foi mostrado acima (só que com a quantidade de informações * número de player jogando) infinitamente para todos os clients.  
Informando sempre qual o estado do jogador X e quais são suas coordenadas.  
Exemplo de Json do Game State que é enviado:  
```
["{\"number\": 1, \"size\": 140, \"score\": 0, \"starting_x\": 0, \"starting_y\": 0, \"p_color\": [255, 0, 0], \"s_color\": [150, 0, 0], \"x\": 0, \"y\": 0, \"dx\": 0, \"dy\": 0, \"coord\": [0, 0, 140, 140], \"is_waiting\": false, \"is_ready\": false, \"is_playing\": true, \"status_message\": \"Aguardando 2 jogadores\"}", 
"{\"number\": 2, \"size\": 140, \"score\": 0, \"starting_x\": 560, \"starting_y\": 0, \"p_color\": [0, 255, 0], \"s_color\": [0, 150, 0], \"x\": 560, \"y\": 0, \"dx\": 0, \"dy\": 0, \"coord\": [560, 0, 140, 140], \"is_waiting\": false, \"is_ready\": false, \"is_playing\": true, \"status_message\": \"Aguardando 2 jogadores\"}"] 
```

### As funções que fazem essa transmissão para o Client são:
* `def send_player_info(self, player, player_socket)` : Linha 194 / Faz o envio do Json com a informação do Player X
* `def recieve_pregame_player_info(self, player, player_socket)`: Linha 210 / que recebe e decodifica o JSON vindo dos Clients no PRÉ JOGO
* `def recieve_game_player_info(self, player, player_socket)`: Linha 218 / que recebe e decodifica o JSON vindo dos Clients no DURANTE JOGO. Essa é diferente da anterior porque ela irá receber frequentemente um bombardeio de informações e irá se conectr com a proxima função para que mantenha o estado do jogo atualizado.
* `def process_game_state(self, player, player_socket)`: Linha 232 / Função que interage com todas as variáveis do jogo (tempo atual do turno e a coordenada de cada jogador).  
Ela que irá realizar a verificação de um player colidiu com o outro: 
```
 for player_object in self.player_objects:
            if player != player_object: # Se o player atual não é ele mesmo
                if player.coord == player_object.coord: # Se a coordenada do player atual é a mesma que a de outro player
                    player.score += 1 # aumenta a pontuação do player atual
                    player.x = player.starting_x # joga o player de volta para a coordenada inicial para resetar o jogo
                    player.y = player.starting_y
                    player.coord = (player.x, player.y, player.size, player.size)
```

* `def send_game_state(self, player_socket)`: a função que irá fazer o envio dos estados do jogo para os clients

## Como é possível que tenha até 4 jogadores e o server fique enviando JSON para tantos clients???
O programa utiliza Multi Thread que faz o processamento de multiplos envios frequentes.  
Lib usada é a nativa do python `threading`.  
```
ready_thread = threading.Thread(target=self.ready_game, args=(player, player_socket,))
            ready_thread.start()
```

# DIAGRAMA DE FUNCIONAMENTO DO PROTOCOLO

Inicia o server e fica escutando  
Conecta algum client.py  
CLIENT --------------------------------- Informa que se conectou ---------------------------------> Server  
                                                                                Server configura o primeiro objeto como jogador Número 1 e cria o json  
  
CLIENT <------------ Envia JSON com todas as informações e aguarda mais jogadores ----------------- Server  
  
CLIENT2 --------------------------------- Informa que se Conectou --------------------------------> Server  
                                                                                Server configura o objeto como jogador Número 2 e cria o json com as duas informações  
  
CLIENT 1 E 2 <--------- Envia Json com as informações dos dois players e espera alteração -------- Server   
O server irá aguardar os 2 players mudarem seus Status `is_waiting` para **False** e `is_ready` para **True**  
Assim que o server receber os Jsons com os estados acima, irá alterar nos dois o atributo `is_playing` para **True**  
E realizará o envio frequente das informações dos estados do Jogo até acabar o Tempo do Round.

