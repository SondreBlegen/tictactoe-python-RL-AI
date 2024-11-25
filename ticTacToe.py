import numpy as np
import pickle
import os
import pygame
import sys

BOARD_ROWS = 3
BOARD_COLS = 3
SQUARE_SIZE = 200
LINE_WIDTH = 15
CIRCLE_WIDTH = 15
CROSS_WIDTH = 25
RADIUS = 60
OFFSET = 50
screen_size = SQUARE_SIZE * 3

COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)

pygame.init()
screen = pygame.display.set_mode((screen_size, screen_size))
pygame.display.set_caption("Tic Tac Toe")


class State:
    def __init__(self, p1, p2):
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        self.p1 = p1
        self.p2 = p2
        self.isEnd = False
        self.boardHash = None
        # init p1 plays first
        self.playerSymbol = 1

    # get unique hash of current board state
    def getHash(self):
        self.boardHash = str(self.board.reshape(BOARD_COLS * BOARD_ROWS))
        return self.boardHash

    def winner(self):
        # row
        for i in range(BOARD_ROWS):
            if sum(self.board[i, :]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[i, :]) == -3:
                self.isEnd = True
                return -1
        # col
        for i in range(BOARD_COLS):
            if sum(self.board[:, i]) == 3:
                self.isEnd = True
                return 1
            if sum(self.board[:, i]) == -3:
                self.isEnd = True
                return -1
        # diagonal
        diag_sum1 = sum([self.board[i, i] for i in range(BOARD_COLS)])
        diag_sum2 = sum([self.board[i, BOARD_COLS - i - 1] for i in range(BOARD_COLS)])
        diag_sum = max(abs(diag_sum1), abs(diag_sum2))
        if diag_sum == 3:
            self.isEnd = True
            if diag_sum1 == 3 or diag_sum2 == 3:
                return 1
            else:
                return -1

        # tie
        # no available positions
        if len(self.availablePositions()) == 0:
            self.isEnd = True
            return 0
        # not end
        self.isEnd = False
        return None

    def availablePositions(self):
        positions = []
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                if self.board[i, j] == 0:
                    positions.append((i, j))  # need to be tuple
        return positions

    def updateState(self, position):
        self.board[position] = self.playerSymbol
        # switch to another player
        self.playerSymbol = -1 if self.playerSymbol == 1 else 1

    # only when game ends
    def giveReward(self):
        result = self.winner()
        # backpropagate reward
        if result == 1:
            self.p1.feedReward(1)
            self.p2.feedReward(0)
        elif result == -1:
            self.p1.feedReward(0)
            self.p2.feedReward(1)
        else:
            self.p1.feedReward(0.1)
            self.p2.feedReward(0.5)

    # board reset
    def reset(self):
        self.board = np.zeros((BOARD_ROWS, BOARD_COLS))
        self.boardHash = None
        self.isEnd = False
        self.playerSymbol = 1

    def play(self, rounds=100):
        for i in range(rounds):
            if i % 1000 == 0:
                print("Rounds {}".format(i))
            while not self.isEnd:
                # Player 1
                positions = self.availablePositions()
                p1_action = self.p1.chooseAction(positions, self.board, self.playerSymbol)
                self.updateState(p1_action)
                if i % 1000 == 0:
                    self.draw_update()
                    pygame.time.wait(500)
                board_hash = self.getHash()
                self.p1.addState(board_hash)
                # check board status if it is end

                win = self.winner()
                if win is not None:
                    self.draw_update()
                    self.giveReward()
                    self.p1.reset()
                    self.p2.reset()
                    self.reset()
                    break

                else:
                    # Player 2
                    positions = self.availablePositions()
                    p2_action = self.p2.chooseAction(positions, self.board, self.playerSymbol)
                    self.updateState(p2_action)
                    if i % 1000 == 0:
                        self.draw_update()
                        pygame.time.wait(500)
                    board_hash = self.getHash()
                    self.p2.addState(board_hash)

                    win = self.winner()
                    if win is not None:
                        self.draw_update()
                        self.giveReward()
                        self.p1.reset()
                        self.p2.reset()
                        self.reset()
                        break

        self.p1.savePolicy()
        self.p2.savePolicy()

    # play with human
    def play2(self):
        while not self.isEnd:
            # Player 1
            positions = self.availablePositions()
            p1_action = self.p1.chooseAction(positions, self.board, self.playerSymbol)
            self.updateState(p1_action)
            self.draw_update()
            win = self.winner()
            if win is not None:
                if win == 1:
                    print(self.p1.name, "wins!")
                    if win == 1:
                        # Check if the winning condition is a row
                        for i in range(BOARD_ROWS):
                            if sum(self.board[i, :]) == 3:
                                pygame.draw.line(screen, COLOR_BLACK, (0, (i + 0.5) * SQUARE_SIZE), (screen_size, (i + 0.5) * SQUARE_SIZE), LINE_WIDTH)
                                break
                        # Check if the winning condition is a column
                        for i in range(BOARD_COLS):
                            if sum(self.board[:, i]) == 3:
                                pygame.draw.line(screen, COLOR_BLACK, ((i + 0.5) * SQUARE_SIZE, 0), ((i + 0.5) * SQUARE_SIZE, screen_size), LINE_WIDTH)
                                break
                        # Check if the winning condition is a diagonal
                        diag_sum1 = sum([self.board[i, i] for i in range(BOARD_COLS)])
                        diag_sum2 = sum([self.board[i, BOARD_COLS - i - 1] for i in range(BOARD_COLS)])
                        if diag_sum1 == 3:
                            pygame.draw.line(screen, COLOR_BLACK, (0, 0), (screen_size, screen_size), LINE_WIDTH)
                        elif diag_sum2 == 3:
                            pygame.draw.line(screen, COLOR_BLACK, (0, screen_size), (screen_size, 0), LINE_WIDTH)
                            
                    font = pygame.font.Font(None, 36)
                    text = font.render(f"{self.p1.name} wins!", True, COLOR_BLUE)
                    text_rect = text.get_rect(center=(screen_size // 2, screen_size // 2))
                    screen.blit(text, text_rect)
                    
                    text2 = font.render(f"Click to play again", True, COLOR_BLUE)
                    text_rect2 = text.get_rect(center=(screen_size // 2, (screen_size // 2) + 60))
                    screen.blit(text2, text_rect2)
                    
                    pygame.display.update()
                    isWaiting = True
                    while isWaiting:
                        for event in pygame.event.get():
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                isWaiting = False
                    
                else:
                    print("tie!")
                self.reset()
                break

            else:
                # Player 2
                positions = self.availablePositions()
                p2_action = self.p2.chooseAction(positions, self.board, self.playerSymbol)
                self.updateState(p2_action)
                self.draw_update()
                win = self.winner()
                if win is not None:
                    if win == -1:
                        print(self.p2.name, "wins!")
                    else:
                        print("tie!")
                    self.reset()
                    break

    def draw_update(self):
        screen.fill(COLOR_WHITE)
        # draw grid
        for row in range(1, BOARD_ROWS):
            pygame.draw.line(screen, COLOR_BLACK, (0, row * SQUARE_SIZE), (screen_size, row * SQUARE_SIZE), LINE_WIDTH)
        for col in range(1, BOARD_COLS):
            pygame.draw.line(screen, COLOR_BLACK, (col * SQUARE_SIZE, 0), (col * SQUARE_SIZE, screen_size), LINE_WIDTH)
        # draw pieces
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                if self.board[row][col] == 1:
                    pygame.draw.line(screen, COLOR_RED, (col * SQUARE_SIZE + OFFSET, row * SQUARE_SIZE + OFFSET),
                                     ((col + 1) * SQUARE_SIZE - OFFSET, (row + 1) * SQUARE_SIZE - OFFSET), CROSS_WIDTH)
                    pygame.draw.line(screen, COLOR_RED, ((col + 1) * SQUARE_SIZE - OFFSET, row * SQUARE_SIZE + OFFSET),
                                     (col * SQUARE_SIZE + OFFSET, (row + 1) * SQUARE_SIZE - OFFSET), CROSS_WIDTH)
                elif self.board[row][col] == -1:
                    pygame.draw.circle(screen, COLOR_RED, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), RADIUS, CIRCLE_WIDTH)
        pygame.display.update()

class Player:
    def __init__(self, name, exp_rate=0.3):
        self.name = name
        self.states = []  # record all positions taken
        self.lr = 0.2
        self.exp_rate = exp_rate
        self.decay_gamma = 0.9
        self.states_value = {}  # state -> value

    def getHash(self, board):
        boardHash = str(board.reshape(BOARD_COLS * BOARD_ROWS))
        return boardHash

    def chooseAction(self, positions, current_board, symbol):
        if np.random.uniform(0, 1) <= self.exp_rate:
            # take random action
            idx = np.random.choice(len(positions))
            action = positions[idx]
        else:
            value_max = -999
            for p in positions:
                next_board = current_board.copy()
                next_board[p] = symbol
                next_boardHash = self.getHash(next_board)
                value = 0 if self.states_value.get(next_boardHash) is None else self.states_value.get(next_boardHash)
                if value >= value_max:
                    value_max = value
                    action = p
        return action

    def addState(self, state):
        self.states.append(state)

    def feedReward(self, reward):
        for st in reversed(self.states):
            if self.states_value.get(st) is None:
                self.states_value[st] = 0
            self.states_value[st] += self.lr * (self.decay_gamma * reward - self.states_value[st])
            reward = self.states_value[st]

    def reset(self):
        self.states = []

    def savePolicy(self):
        file_name = 'policy_' + str(self.name)
        with open(file_name, 'wb') as fw:
            pickle.dump(self.states_value, fw)

    def loadPolicy(self, file):
        fr = open(file, 'rb')
        self.states_value = pickle.load(fr)
        fr.close()


class HumanPlayer:
    def __init__(self, name):
        self.name = name

    def chooseAction(self, positions, board, symbol):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    row = pos[1] // SQUARE_SIZE
                    col = pos[0] // SQUARE_SIZE
                    action = (row, col)
                    if action in positions:
                        return action

    def addState(self, state):
        pass

    def feedReward(self, reward):
        pass

    def reset(self):
        pass


if __name__ == "__main__":
    # training
    if not os.path.isfile("policy_p1") or not os.path.isfile("policy_p2"):
        p1 = Player("p1")
        p2 = Player("p2")

        st = State(p1, p2)
        print("training...")
        st.play(rounds=50000)

    # play with human
    p1 = Player("computer", exp_rate=0)
    p1.loadPolicy("policy_p1")

    p2 = HumanPlayer("human")

    st = State(p1, p2)
    while True:
        st.play2()