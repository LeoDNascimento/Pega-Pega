import pygame, socket, threading, json

#DEST_IP tem que ter formato '192.168.1.*'
DEST_IP = socket.gethostbyname(socket.gethostname())
DEST_PORT = 12345
#-----------------------------------------------------------------------------------------
#Define Classes
class Connection():
    def __init__(self):
        self.encoder = "utf-8"
        self.header_length = 10

        #Create a socket and connect
        self.player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_socket.connect((DEST_IP, DEST_PORT))


class Player():
    def __init__(self, connection):
        packet_size = connection.player_socket.recv(connection.header_length).decode(connection.encoder)
        player_info_json = connection.player_socket.recv(int(packet_size))
        player_info = json.loads(player_info_json)

        self.number = player_info['number']
        self.size = player_info['size']

        self.starting_x = player_info['starting_x']
        self.starting_y = player_info['starting_y']
        self.p_color = player_info['p_color']
        self.s_color = player_info['s_color']

        self.x = player_info['x']
        self.y = player_info['y']
        self.dx = player_info['dx']
        self.dy = player_info['dy']
        self.coord = player_info['coord']

        self.is_waiting = player_info['is_waiting']
        self.is_ready = player_info['is_ready']
        self.is_playing = player_info['is_playing']
        self.status_message = player_info['status_message']


    def set_player_info(self, player_info):
        self.is_waiting = player_info['is_waiting']
        self.is_ready = player_info['is_ready']
        self.is_playing = player_info['is_playing']


    def update(self):
        keys = pygame.key.get_pressed()
        player_rect = pygame.draw.rect(display_surface, self.p_color, self.coord)

        if self.is_playing:
            if keys[pygame.K_UP] and player_rect.top > 0:
                self.dx = 0
                self.dy = -1*self.size
            elif keys[pygame.K_DOWN] and player_rect.bottom < WINDOW_HEIGHT:
                self.dx = 0
                self.dy = 1*self.size
            elif keys[pygame.K_LEFT] and player_rect.left > 0:
                self.dx = -1*self.size
                self.dy = 0
            elif keys[pygame.K_RIGHT] and player_rect.right < WINDOW_WIDTH:
                self.dx = 1*self.size
                self.dy = 0
            else:
                self.dx = 0
                self.dy = 0

            self.x += self.dx
            self.y += self.dy
            self.coord = (self.x, self.y, self.size, self.size)


    def reset_player(self):
        self.x = self.starting_x
        self.y = self.starting_y
        self.coord = (self.x, self.y, self.size, self.size)

        self.is_waiting = False
        self.is_ready = True
        self.is_playing = False
        self.status_message = "Aguardando novos jogadores..."


class Game():
    def __init__(self, connection, player, total_players):
        self.connection = connection
        self.player = player
        self.total_players = total_players
        self.is_active = False

        self.player_count = self.player.number - 1

        self.game_state = []

        self.round_time = ROUND_TIME
        self.high_score = 0
        self.winning_player = 0

        waiting_thread = threading.Thread(target=self.recieve_pregame_state)
        waiting_thread.start()


    def ready_game(self):

        self.player.is_waiting = False
        self.player.is_ready = True
        self.player.status_message = "Aguardando outros jogadores..."

        #Send updated status to the server
        self.send_player_info()

        start_thread = threading.Thread(target=self.start_game)
        start_thread.start()


    def start_game(self):

        while True:
            self.recieve_player_info()
            if self.player.is_playing:
                self.is_active = True
                self.player.is_ready = False
                self.player.status_message = "Play!"
                break


    def reset_game(self):

        self.round_time = ROUND_TIME
        self.winning_player = 0
        self.high_score = 0

        self.player.reset_player()

        self.send_player_info()

        start_thread = threading.Thread(target=self.start_game)
        start_thread.start()


    def send_player_info(self):

        player_info = {
            'coord': self.player.coord,
            'is_waiting': self.player.is_waiting,
            'is_ready': self.player.is_ready,
            'is_playing': self.player.is_playing,
        }

        player_info_json = json.dumps(player_info)
        header = str(len(player_info_json))
        while len(header) < self.connection.header_length:
            header += " "
        self.connection.player_socket.send(header.encode(self.connection.encoder))
        self.connection.player_socket.send(player_info_json.encode(self.connection.encoder))


    def recieve_player_info(self):
        packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
        player_info_json = self.connection.player_socket.recv(int(packet_size))
        player_info = json.loads(player_info_json)

        self.player.set_player_info(player_info)


    def recieve_pregame_state(self):   
        while self.player_count < self.total_players:
            packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
            game_state_json = self.connection.player_socket.recv(int(packet_size))
            game_state = json.loads(game_state_json)
            self.game_state = game_state

            self.player_count += 1
        
        #All players have joined 
        self.player.status_message = "Press Enter para jogar!"


    def recieve_game_state(self):
        packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
        game_state_json = self.connection.player_socket.recv(int(packet_size))
        game_state = json.loads(game_state_json)

        self.game_state = game_state

        packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
        self.round_time = self.connection.player_socket.recv(int(packet_size)).decode(self.connection.encoder)

        self.process_game_state()


    def process_game_state(self):
        current_scores = []

        for player in self.game_state:
            player = json.loads(player) 
            if player['number'] == self.player.number:
                self.player.coord = player['coord']
                self.player.x = self.player.coord[0]
                self.player.y = self.player.coord[1]
            
            if player['score'] > self.high_score:
                self.winning_player = player['number']
                self.high_score = player['score']
            current_scores.append(player['score'])
        
        count = 0
        for score in current_scores:
            if score == self.high_score:
                count += 1
        if count > 1:
            self.winning_player = 0


    def update(self):

        if self.player.is_playing:
            self.player.update()

            if int(self.round_time) == 0:
                self.player.is_playing = False
                self.player.is_ready = False
                self.player.is_waiting = True
                self.player.status_message = "Game Over! Enter to play again"

            self.send_player_info()
            self.recieve_game_state()


    def draw(self):

        for player in self.game_state:
            player = json.loads(player)
            if player['number'] == self.winning_player:
                display_surface.fill(player['s_color'])
        current_scores = []

        for player in self.game_state:
            player = json.loads(player)

            score = "P" + str(player['number']) + ": " + str(player['score'])
            score_text = font.render(score, True, WHITE)
            score_rect = score_text.get_rect()
            if player['number'] == 1:
                score_rect.topleft = (player['starting_x'], player['starting_y'])
            elif player['number'] == 2:
                score_rect.topright = (player['starting_x'], player['starting_y'])
            elif player['number'] == 3:
                score_rect.bottomleft = (player['starting_x'], player['starting_y'])
            else:
                score_rect.bottomright = (player['starting_x'], player['starting_y'])
            current_scores.append((score_text, score_rect))

            pygame.draw.rect(display_surface, player['p_color'], player['coord'])

        pygame.draw.rect(display_surface, self.player.p_color, self.player.coord)
        pygame.draw.rect(display_surface, MAGENTA, self.player.coord, int(self.player.size/10))


        for score in current_scores:
            display_surface.blit(score[0], score[1])

        time_text = font.render("Round Time: " + str(self.round_time), True, WHITE)
        time_rect = time_text.get_rect()
        time_rect.center = (WINDOW_WIDTH//2, 15)
        display_surface.blit(time_text, time_rect)


        status_text = font.render(self.player.status_message, True, WHITE)
        status_rect = status_text.get_rect()
        status_rect.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
        display_surface.blit(status_text, status_rect)


#Cria a conexão e pegar as informações da janela do jogo do server
my_connection = Connection()
packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
room_size = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))
packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
round_time = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))
packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
fps = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))
packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
total_players = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))

#Initialize pygame
pygame.init()

WINDOW_WIDTH = room_size
WINDOW_HEIGHT = room_size
ROUND_TIME = round_time
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MAGENTA = (155, 0, 155)
FPS = fps
clock = pygame.time.Clock()
font = pygame.font.SysFont('gabriola', 28)

#Janela do game
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("~~Pega-pega~~")


my_player = Player(my_connection)
my_game = Game(my_connection, my_player, total_players)

#game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if my_player.is_waiting and my_game.is_active:
                    my_game.reset_game()
                if my_player.is_waiting and my_game.player_count == my_game.total_players:
                    my_game.ready_game()
    
    display_surface.fill(BLACK)

    my_game.update()
    my_game.draw()

    pygame.display.update()
    clock.tick(FPS)