# Program to group students for a course project based on their preferences.

## These preferences are:
* team size
* whom a student wants to work with
* whom a student don't want to work with

## Prerequisites
* Install the package `numpy`. Execute the command `sudo pip install numpy`

## Usage
`python assign.py [k] [m] [n]`
* k -> Time required to grade each assignment
* m -> Time required to complain about being teamed with a foe
* n -> Time required to complain about not being teamed with a friend

## References
1) http://ieeexplore.ieee.org/document/5518761/
    * Borrowing terms like friends and foes from this paper
    * Referring the cost calculation of this paper to implement my own cost calculation
2) http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.521.2649&rep=rep1&type=pdf
    * Implementing the Squeaky Wheel algorithm as mentioned in this paper