import socket, threading, json, time

#---------------------------------------------------------------------------------------------
HOST_IP = socket.gethostbyname(socket.gethostname())
HOST_PORT = 12345

#Variaveis para  janela do pygame
ROOM_SIZE = 700
PLAYER_SIZE = 140
ROUND_TIME = 30
FPS = 15
TOTAL_PLAYERS = 2

while ROOM_SIZE % PLAYER_SIZE != 0:
    PLAYER_SIZE += 1

if TOTAL_PLAYERS > 4:
    TOTAL_PLAYERS = 4
#---------------------------------------------------------------------------------------------
class Connection():
    def __init__(self):
        self.encoder = 'utf-8'
        self.header_length = 10

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST_IP, HOST_PORT))
        self.server_socket.listen()


class Player():
    def __init__(self, number):
        self.number = number
        self.size = PLAYER_SIZE
        self.score = 0

        if self.number == 1:
            self.starting_x = 0
            self.starting_y = 0
            self.p_color = (255, 0, 0)
            self.s_color = (150, 0, 0)
        elif self.number == 2:
            self.starting_x = ROOM_SIZE - PLAYER_SIZE
            self.starting_y = 0
            self.p_color = (0, 255, 0)
            self.s_color = (0, 150, 0)
        elif self.number == 3:
            self.starting_x = 0
            self.starting_y = ROOM_SIZE - PLAYER_SIZE
            self.p_color = (0, 0, 255)
            self.s_color = (0, 0, 150)
        elif self.number == 4:
            self.starting_x = ROOM_SIZE - PLAYER_SIZE
            self.starting_y = ROOM_SIZE - PLAYER_SIZE
            self.p_color = (255, 255, 0)
            self.s_color = (150, 150, 0)
        else:
            print("Mais jogadores que o esperado tentando entrar...")

        self.x = self.starting_x
        self.y = self.starting_y
        self.dx = 0
        self.dy = 0
        self.coord = (self.x, self.y, self.size, self.size)

        self.is_waiting = True
        self.is_ready = False
        self.is_playing = False
        self.status_message = f"Aguardando {TOTAL_PLAYERS} jogadores"


    def set_player_info(self, player_info):
        self.coord = player_info['coord']
        self.is_waiting = player_info['is_waiting']
        self.is_ready = player_info['is_ready']
        self.is_playing = player_info['is_playing']


    def reset_player(self):
        self.score = 0


class Game():
    def __init__(self, connection):
        self.connection = connection
        self.player_count = 0
        self.player_objects = []
        self.player_sockets = []
        self.round_time = ROUND_TIME


    def connect_players(self):

        while self.player_count < TOTAL_PLAYERS:

            player_socket, player_address = self.connection.server_socket.accept()

            header = str(len(str(ROOM_SIZE)))
            while len(header) < self.connection.header_length:
                header += " "  
            player_socket.send(header.encode(self.connection.encoder))
            player_socket.send(str(ROOM_SIZE).encode(self.connection.encoder))

            header = str(len(str(ROUND_TIME)))
            while len(header) < self.connection.header_length:
                header += " "  
            player_socket.send(header.encode(self.connection.encoder))
            player_socket.send(str(ROUND_TIME).encode(self.connection.encoder))

            header = str(len(str(FPS)))
            while len(header) < self.connection.header_length:
                header += " "  
            player_socket.send(header.encode(self.connection.encoder))
            player_socket.send(str(FPS).encode(self.connection.encoder))

            header = str(len(str(TOTAL_PLAYERS)))
            while len(header) < self.connection.header_length:
                header += " "  
            player_socket.send(header.encode(self.connection.encoder))
            player_socket.send(str(TOTAL_PLAYERS).encode(self.connection.encoder))

            self.player_count += 1
            player = Player(self.player_count)
            self.player_objects.append(player)
            self.player_sockets.append(player_socket)
            print(f"New player joining from {player_address}...Total players: {self.player_count}")

            player_info_json = json.dumps(player.__dict__)
            header = str(len(player_info_json))
            while len(header) < self.connection.header_length:
                header += " "
            player_socket.send(header.encode(self.connection.encoder))
            player_socket.send(player_info_json.encode(self.connection.encoder))

            self.broadcast()

            ready_thread = threading.Thread(target=self.ready_game, args=(player, player_socket,))
            ready_thread.start()

        print(f"{TOTAL_PLAYERS} jogadores.  Atingiu o máximo.")


    def broadcast(self):
        game_state = []

        for player_object in self.player_objects:
            player_json = json.dumps(player_object.__dict__)
            game_state.append(player_json)

        game_state_json = json.dumps(game_state)
        header = str(len(game_state_json))
        while len(header) < self.connection.header_length:
            header += " "
        for player_socket in self.player_sockets:
            player_socket.send(header.encode(self.connection.encoder))
            player_socket.send(game_state_json.encode(self.connection.encoder))


    def ready_game(self, player, player_socket):

        self.recieve_pregame_player_info(player, player_socket)

        self.reset_game(player)


        if player.is_ready:
            while True:

                game_start = True
                for player_object in self.player_objects:
                    if player_object.is_ready == False:
                        game_start = False
                    
                if game_start:
                    player.is_playing = True
                    
                    self.start_time = time.time()
                    break
            
            self.send_player_info(player, player_socket)

            recieve_thread = threading.Thread(target=self.recieve_game_player_info, args=(player, player_socket,))
            recieve_thread.start()
                     

    def reset_game(self, player):

        self.round_time = ROUND_TIME

        player.reset_player()


    def send_player_info(self, player, player_socket):

        player_info = {
            'is_waiting': player.is_waiting,
            'is_ready': player.is_ready,
            'is_playing': player.is_playing,
        }

        player_info_json = json.dumps(player_info)
        header = str(len(player_info_json))
        while len(header) < self.connection.header_length:
            header += " "
        player_socket.send(header.encode(self.connection.encoder))
        player_socket.send(player_info_json.encode(self.connection.encoder))
        

    def recieve_pregame_player_info(self, player, player_socket):
        packet_size = player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
        player_info_json = player_socket.recv(int(packet_size))
        player_info = json.loads(player_info_json)

        player.set_player_info(player_info)


    def recieve_game_player_info(self, player, player_socket):
        while player.is_playing:
            packet_size = player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
            player_info_json = player_socket.recv(int(packet_size))
            player_info = json.loads(player_info_json)

            player.set_player_info(player_info)

            self.process_game_state(player, player_socket)

        ready_thread = threading.Thread(target=self.ready_game, args=(player, player_socket))
        ready_thread.start()


    def process_game_state(self, player, player_socket):

        self.current_time = time.time()
        self.round_time = ROUND_TIME - int(self.current_time - self.start_time)

        for player_object in self.player_objects:
            if player != player_object:
                if player.coord == player_object.coord:
                    player.score += 1
                    player.x = player.starting_x
                    player.y = player.starting_y
                    player.coord = (player.x, player.y, player.size, player.size)

        self.send_game_state(player_socket)


    def send_game_state(self, player_socket):
        game_state = []

        for player_object in self.player_objects:
            player_json = json.dumps(player_object.__dict__)
            game_state.append(player_json)

        game_state_json = json.dumps(game_state)
        header = str(len(game_state_json))
        while len(header) < self.connection.header_length:
            header += " "
        player_socket.send(header.encode(self.connection.encoder))
        player_socket.send(game_state_json.encode(self.connection.encoder))

        header = str(len(str(self.round_time)))
        while len(header) < self.connection.header_length:
            header += " "
        player_socket.send(header.encode(self.connection.encoder))
        player_socket.send(str(self.round_time).encode(self.connection.encoder))


#Start the server
my_connection = Connection()
my_game = Game(my_connection)

#Listen for incomming connections
print("Server está rodando e esperando...\n")
my_game.connect_players()