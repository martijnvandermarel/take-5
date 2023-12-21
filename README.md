# TAKE 5
This is a project for simulating the card game TAKE 5. 
Aside from implementing the game mechanics, the project is also meant for developing algorithms for optimal strategies, 
and playing these strategies against each other.

## BUILD YOUR OWN BOT
The main goal of the project is to design and implement your own strategy. For this, an abstract base class `Player` is available. The base player class has two methods that may be implemented:
* `choose_card`: Each turn, a player has to choose a card to play based on their hand and the current state of the board.
* `choose_row`: If a player plays a card lower than any of the row heads currently on the board, they have to choose a row which they must take.

Some examples of player classes are already available in the code.

## MANUAL PLAY
Using the `ManualPlayer` player class you can play the game with manual inputs via the terminal. Multiplayer is also supported, though you will be able to see each other's hands in the terminal.

## TODOS
There are a couple of todos:
* Implement historic cards as input to the card choosing method
* Implement the official variants of the game, with slightly different rulesets

