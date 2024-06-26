"""
Author: Evan Schneider
Modified: 4/28/2024

Adapted from HMC CS60

TODO Update this program header
"""

from preferences import Preferences
from gameData import GameData
from boardDisplay import BoardDisplay

import pygame
from enum import Enum
from queue import Queue

class Controller():
    def __init__(self):
        # The current state of the board
        self.__data = GameData()
        # The display
        self.__display = BoardDisplay()
        # How many frames have passed
        self.__numCycles = 0
        self.score = 0


        # Attempt to load any sounds and images
        try:
            pygame.mixer.init()
            self.__audioEat = pygame.mixer.Sound(Preferences.EAT_SOUND)
            self.__display.headImage = pygame.image.load(Preferences.HEAD_IMAGE)
        except:
            print("Problem error loading audio / images")
            self.__audioEat = None

        # Initialize the board for a new game
        self.startNewGame()
        
    def startNewGame(self):
        """ Initializes the board for a new game """

        # Place the snake on the board
        self.__data.placeSnakeAtStartLocation()

    def gameOver(self):
        """ Indicate that the player has lost """
        self.__data.setGameOver()

    def run(self):
        """ The main loop of the game """

        # Keep track of the time that's passed in the game 
        clock = pygame.time.Clock()

        # Loop until the game ends
        while not self.__data.getGameOver():
            # Run the main behavior
            self.cycle() 
            # Sleep
            clock.tick(Preferences.SLEEP_TIME)

    def cycle(self):
        """ The main behavior of each time step """

        # Check for user input
        self.checkKeypress()
        # Update the snake state
        self.updateSnake()
        # Update the food state
        self.updateFood()
        # Increment the number of cycles
        self.__numCycles += 1
        # Update the display based on the new state
        self.__display.updateGraphics(self.__data)

    def handleFoodCollision(self):
        """Handle collision between snake and food."""
        if self.__data.foodCollision():
            self.__data.increaseScore()  # Increase the score when the snake eats food
            self.score += 1  # Increment the score


    def checkKeypress(self):
        """ Update the game based on user input """
        # Check for keyboard input
        for event in pygame.event.get():
            # Quit the game
            if event.type == pygame.QUIT:
                self.gameOver()
            # Change the snake's direction based on the keypress
            elif event.type == pygame.KEYDOWN:
                # Reverse direction of snake
                if event.key in self.Keypress.REVERSE.value:
                    self.reverseSnake()
                # Enter AI mode
                elif event.key in self.Keypress.AI.value:
                    self.__data.setAIMode()
                # Change directions
                if event.key in self.Keypress.LEFT.value:
                    self.__data.setDirectionWest()
                elif event.key in self.Keypress.RIGHT.value:
                    self.__data.setDirectionEast()
                elif event.key in self.Keypress.UP.value:
                    self.__data.setDirectionNorth()
                elif event.key in self.Keypress.DOWN.value:
                    self.__data.setDirectionSouth()

    def updateSnake(self):
        """ Move the snake forward one step, either in the current 
            direction, or as directed by the AI """

        # Move the snake once every REFRESH_RATE cycles
        if self.__numCycles % Preferences.REFRESH_RATE == 0:
            # Find the next place the snake should move
            if self.__data.inAIMode():
                nextCell = self.getNextCellFromBFS()
            else:
                nextCell = self.__data.getNextCellInDir()
            try:
                # Move the snake to the next cell
                self.advanceSnake(nextCell)
            except:
                print("Failed to advance snake")

    def advanceSnake(self, nextCell):
        """ Update the state of the world to move the snake's head to the given cell """

        # If we run into a wall or the snake, it's game over
        if nextCell.isWall() or nextCell.isBody():
            self.gameOver()
        
        # If we eat food, update the state of the board
        elif nextCell.isFood():
            self.playSound_eat()
            # Tell __data that we ate food!
            self.__data.ateFood(nextCell)

        # Otherwise, move the snake to the empty cell
        else:
            self.__data.moveSnake(nextCell)

    def updateFood(self):
        """ Add food every FOOD_ADD_RATE cycles or if there is no food """
        if self.__data.noFood() or (self.__numCycles % Preferences.FOOD_ADD_RATE == 0):
            self.__data.addFood()

    def getNextCellFromBFS(self):
        """ Uses BFS to search for the food closest to the head of the snake. Returns the *next* step the snake should take along the shortest path
            to the closest food cell. """
        
        # Prepare all the tiles to search
        self.__data.resetCellsForSearch()

        # Initialize a queue to hold the tiles to search
        cellsToSearch = Queue()

        # Add the head to the queue and mark it as added
        head = self.__data.getSnakeHead()
        head.setAddedToSearchList()
        cellsToSearch.put(head)

        # Search!
        while not cellsToSearch.empty():
            current_cell = cellsToSearch.get()

            # Check if the current cell is the food cell
            if current_cell.isFood():
                # Get the first cell in the path
                first_cell_in_path = self.getFirstCellInPath(current_cell)

                # Determine the next cell in the path
                next_cell_in_path = first_cell_in_path.getParent()

                # Return the next cell in the path
                return next_cell_in_path

            # Add neighboring cells to the queue if not visited
            neighbors = self.__data.getNeighbors(current_cell)
            for neighbor in neighbors:
                if not neighbor.getAddedToSearchList():
                    neighbor.setAddedToSearchList()
                    cellsToSearch.put(neighbor)

        # If no path to food found, return None or a random neighbor
        return None

    def getFirstCellInPath(self, foodCell):
        """ Returns the first cell in the path from the head to the food cell. """

        # Initialize the current cell as the food cell
        current_cell = foodCell

        # Traverse back along the path until finding the first cell
        while current_cell.getParent() is not None:
            current_cell = current_cell.getParent()

        # Return the first cell in the path
        return current_cell
        
    def reverseSnake(self):
        # Get the current snake cells
        snakeCells = self.__data.getSnakeCells()

        # Check if the snake has at least 2 cells
        if len(snakeCells) >= 2:
            # Reverse the order of the snake cells
            snakeCells.reverse()

            # Update the snake cells in the game data
            self.__data.setSnakeCells(snakeCells)

            # Determine the new direction based on the positions of the head and neck
            head, neck = snakeCells[0], snakeCells[1]
            directions = {
                (-1, 0): self.__data.setDirectionNorth,  # Up
                (1, 0): self.__data.setDirectionSouth,   # Down
                (0, -1): self.__data.setDirectionWest,  # Left
                (0, 1): self.__data.setDirectionEast    # Right
            }
            delta_row, delta_col = head.getRow() - neck.getRow(), head.getCol() - neck.getCol()
            new_direction = directions.get((delta_row, delta_col), None)
            if new_direction:
                new_direction()
        else:
            print("Snake has fewer than 2 cells, cannot reverse direction.")
            pass

    def playSound_eat(self):
        """ Plays an eating sound """
        if self.__audioEat:
            pygame.mixer.Sound.play(self.__audioEat)
            pygame.mixer.music.stop()

    class Keypress(Enum):
        """ An enumeration (enum) defining the valid keyboard inputs 
            to ensure that we do not accidentally assign an invalid value.
        """
        UP = pygame.K_i, pygame.K_UP        # i and up arrow key
        DOWN = pygame.K_k, pygame.K_DOWN    # k and down arrow key
        LEFT = pygame.K_j, pygame.K_LEFT    # j and left arrow key
        RIGHT = pygame.K_l, pygame.K_RIGHT  # l and right arrow key
        REVERSE = pygame.K_r,               # r
        AI = pygame.K_a,                    # a


if __name__ == "__main__":
    Controller().run()