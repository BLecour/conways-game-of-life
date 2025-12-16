# Conway's Game of Life

Implemented using [NVIDIA Warp](https://github.com/NVIDIA/warp) and [PyGame](https://github.com/pygame/pygame). Conway's Game of Life is a cellular automaton where each cell's state (living or dead) is based off of its direct neighbours. The rules for each cell are:
1. A live cell with fewer than two live neighbours dies.
2. A live cell with two or three live neighbours lives on.
3. A live cell with more than three live neighbours dies.
4. A dead cell with exactly three neighbours becomes a live cell.

It's fascinating how such a simple game can be used to create incredibly complex designs. An example of a [Gosper glider gun](https://en.wikipedia.org/wiki/Gun_(cellular_automaton)) using my implementation can be seen below:

<img src="https://github.com/user-attachments/assets/fac5e833-32f8-42c4-83d4-e972b3e66edc" width="500" height="500" />

## Usage

To use the program, download main.py and execute it using ```python main.py <fps>``` where fps is the number of times per second the cell states will be updated. The fps must be between 1 and 60 and if none is provided, a default value of 30fps is used.
