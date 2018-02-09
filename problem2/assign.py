#!/usr/bin/env python
#
# assign.py     : Program to group students for a course project based on their preferences in
#                 team size, whom to want to work with, and whom they don't want to work with
#
# Prerequisites : Install the package 'numpy'
#                 Execute the command `sudo pip install numpy`
#
# Usage         : python assign.py [k] [m] [n]
#                  where k -> Time required to grade each assignment
#                        m -> Time required to complain about being teamed with a foe
#                        n -> Time required to complain about not being teamed with a friend
#
# References (1): http://ieeexplore.ieee.org/document/5518761/
#                     Borrowing terms like friends and foes from this paper
#                     Referring the cost calculation of this paper to implement my own cost calculation
#            (2): http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.521.2649&rep=rep1&type=pdf
#                     Implementing the Squeaky Wheel algorithm as mentioned in this paper
#
#
# Questions:
# Q) How we formulated the search problem?
# A) This problem could be formulated into a search problem by thinking about the mapping of students
#    into teams as being a state/node. By following this abstraction, we can assume an initial state
#    and keep looking for better states.
#
# Q) What is the state space?
# A) The state space for this problem is exponential.
#    Every student could be in a one member, two member, or a three member team.
#    For multi member teams, there could be any remaining students in the team
#    Essentially, the state state is exponential and enormous.
#    As an example, there are 2 states for 2 students, 5 states for 3 students, 11 states for 4 students and so on.
#
# Q) What is the successor function?
# A) The successor function in this problem is 'Try to pacify the unhappiest student'.
#    Programmatically, this works in a three-step process:
#    i)   Calculate time consumed by every student in a particular state (team configuration)
#    ii)  Pick the student with the highest cost (consuming the most time)
#    iii) Try to pacify the student by keeping them in a team which lowers the cost most
#    iv)  If the list of unhappy students is not empty, repeat the process for the next unhappiest
#         student
#
# Q) What is the initial state?
# A) No initial state was specified in this problem. Therefore, we assume an initial state where every
#    student is in a separate team. But we do not feed this state to the main algorithm. Instead, we
#    try to find a better state by using the 'Squeaky Wheel Algorithm' and then feed the main algorithm
#    with this state.
#
# Q) What are the edge weights?
# A) The reduction in cost (time) in moving from one state to another could be assumed to be the
#    edge weight.
#
# Q) What is the goal state?
# A) This is an NP hard problem, since there are exponential number of states, and for deciding whether the
#    given state is optimal, we need to find cost for all the exponential number of states. Therefore, we
#    decided to use a different mechanism, where we check whether the best state changed in the last 30 moves
#    or not. If it did not, we assume that it is the optimal state
#
# Q) How does your search algorithm work?
# A) We have employed local search, where we assume an initial state, and try to determine the next state
#    greedily. Essentially, at a given state, we try to pacify all the students one by one, picking the
#    unhappiest student (incurring most cost), and try to find a team for them that will result in the least cost.
#    Local search does not guarantee an optimal solution.
#
# Q) What problems did you face?
# A) We were able to model this question into a search problem pretty quickly, but finding existing computer-
#    science research that models this problem was very difficult. We spent a lot of hours online, scanned several
#    research papers trying to find an algorithm that fits the problem. Ultimately, we ended up with a very raw
#    looking local search algorithm.
#
# Q) What assumptions have you made?
# A) The only assumption we have made is that after implementing these 2 algorithms, we reach a satisfactorily
#    sub-optimal state.
#

import sys
from Queue import PriorityQueue
from collections import defaultdict

import numpy

# Constants
max_team_size = 3          # The maximum team size allowed
threshold_iterations = 300  # Program will terminate if the best state does not change in these many iterations

# Global variables
student_dict = dict()      # Global dictionary to store student object wrt student id
assn_grading = 0           # Time spent in grading assignment for one team
size_complaint = 1         # Time spent by a student to complain about their team size
friend_complaint = 0       # Time spent by a student to complain about not being grouped with a friend
foe_complaint = 0          # Time spent by a student to complain about being grouped with a foe

tabu_dict = dict()


class Student:
    """ Object representation of the student
    """
    def __init__(self, student_id, student_name, pref_team_size, friend_list, foe_list):
        """ Constructor
        :param student_id:     ID of the student
        :param student_name:   Name of the student
        :param pref_team_size: Preferred team size of the student
        :param friend_list:    List of people with whom the student wants to work with
        :param foe_list:       List of people with whom the student does not want to work
        """
        global max_team_size
        self.student_id = student_id
        self.student_name = student_name
        self.pref_team_size = pref_team_size
        self.friend_list = friend_list
        self.foe_list = foe_list

    def __str__(self):
        """ Returns a string representation of the Student object to be printed
        :return: String representation of the Student object
        """
        return 'Student ID = %s\nStudent name = %s\nPref team size = %s\nFriends = %s\nFoes = %s\n' \
               % (str(self.student_id), self.student_name, str(self.pref_team_size),
                  str(self.friend_list), str(self.foe_list))

    def calculate_total_cost(self, team):
        """ Calculates the total time taken by the student for complaining
        :param team: Set of the team members
        :return:     Total time taken by the student for complaining
        """
        global size_complaint, friend_complaint, foe_complaint, max_team_size
        curr_size_complaint = size_complaint if self.pref_team_size != len(team) else 0
        friend_count_not_in_team = min(len(self.friend_list), max_team_size) - \
                                   len(list(team.intersection(self.friend_list)))
        foe_count_in_team = len(list(team.intersection(self.foe_list)))
        total_cost = curr_size_complaint + friend_count_not_in_team * friend_complaint + \
                     foe_count_in_team * foe_complaint
        return total_cost


class State:
    """ State is the current mapping of student into teams
    """
    def __init__(self, student_to_team_map):
        """ Constructor
        :param student_to_team_map: Dictionary mapping student id to team id
        """
        global assn_grading
        self.student_to_team_map = student_to_team_map
        self.team_to_student_map = self.build_team_to_student_map()
        self.assn_grading_cost = assn_grading * len(self.team_to_student_map)
        self.student_cost_queue = PriorityQueue()
        self.total_cost = self.assn_grading_cost
        self.calculate_costs_for_all()

    def calculate_costs_for_all(self):
        """ Calculates individual and total cost for all the students
            Keeps the individual costs in a max priority queue
        """
        global student_dict
        for student_id, team_number in self.student_to_team_map.iteritems():
            team = self.team_to_student_map[team_number]
            student_cost = student_dict[student_id].calculate_total_cost(team)
            if student_cost > 0:
                self.student_cost_queue.put((-1 * student_cost, student_id))  # Making it Max Heap
                self.total_cost += student_cost

    def __str__(self):
        """Returns a string representation of the State object to be printed
        :return: String representation of the State object
        """
        global student_dict
        state_str = ''
        for team_set in self.team_to_student_map.values():
            state_str += (' '.join([student_dict[student_id].student_name for student_id in team_set]) + '\n')
        state_str += str(self.total_cost)
        return state_str

    def build_team_to_student_map(self):
        """ Builds a dictionary that maps team number to a set of students
            from the dictionary that maps a student to a team number
        :return: Dictionary that maps team number to a set of students
        """
        team_to_student_map = defaultdict(set)
        for student_id, team_number in self.student_to_team_map.iteritems():
            team_to_student_map[team_number].add(student_id)
        return team_to_student_map

    def cost_of_placing_student_in_team(self, student_id, team_num):
        """ Calculates the cost of placing a student in a team
        :param student_id: ID of student to be placed in the team
        :param team_num:   Team number of the team where student is to be placed
        :return: Change in cost if student is placed in the team
        """
        global student_dict
        global friend_complaint, foe_complaint, size_complaint, assn_grading
        student = student_dict[student_id]
        team = self.team_to_student_map[team_num]
        curr_team_size = len(team)
        curr_assn_grading = 0 if curr_team_size > 1 else assn_grading
        team_size_complaints = 0 if curr_team_size + 1 == student.pref_team_size else 1
        friend_count_in_team = len(list(team.intersection(student.friend_list)))
        foes_count_in_team = len(list(team.intersection(student.foe_list)))
        for team_member_id in team:
            team_member = student_dict[team_member_id]
            if team_member.pref_team_size != curr_team_size + 1:
                team_size_complaints += 1
            if student.student_id in team_member.friend_list:
                friend_count_in_team += 1
            elif student.student_id in team_member.foe_list:
                foes_count_in_team += 1
        total_cost = (team_size_complaints * size_complaint) + (foes_count_in_team * foe_complaint) - \
                     (friend_count_in_team * friend_complaint) - curr_assn_grading
        return total_cost

    def assign_student_to_team(self, student_id, next_team_num):
        """ Assigns student to a team
        :param student_id:    ID of the student that has to be assigned to a team
        :param next_team_num: Team number of the team where the student is to be assigned
        """
        if student_id in self.student_to_team_map:
            curr_team_num = self.student_to_team_map[student_id]
            self.team_to_student_map[curr_team_num].remove(student_id)
        self.student_to_team_map[student_id] = next_team_num
        self.team_to_student_map[next_team_num].add(student_id)


def replace_student_name_with_id(student_name_to_id_map):
    """ Initially the student object contain a names in friend list and foe list
        This function replaces those student names with student ids
    :param student_name_to_id_map: Dictionary that maps student name to student id
    """
    global student_dict
    for student in student_dict.values():
        new_friend_list = list()
        for friend_name in student.friend_list:
            new_friend_list.append(student_name_to_id_map[friend_name])
        student.friend_list = new_friend_list
        new_foe_list = list()
        for foe_name in student.foe_list:
            new_foe_list.append(student_name_to_id_map[foe_name])
        student.foe_list = new_foe_list


def parse_file(file_path):
    """ Parses the provided file to fetch the student preferences
    :param file_path: Path of the file to be parsed
    :return:          Dictionary that maps student name to student id
    """
    global student_dict
    student_name_to_id_map = dict()
    fh = open(file_path, 'r')
    lines = fh.read().splitlines()
    fh.close()
    student_id = 0
    for line in lines:
        fields = line.split(' ')
        student_name = fields[0]
        pref_team_size = int(fields[1])
        pref_team_size = min(max(1, pref_team_size), max_team_size)  # Cleansing preferred team size
        friends = fields[2].split(',') if fields[2] != '_' else []
        foes = fields[3].split(',') if fields[3] != '_' else []
        redundant_list = list(set(friends).intersection(foes))
        redundant_list.append(student_name)
        # Removing redundant entries from student's friend list
        friends = [x for x in friends if x not in redundant_list]
        # Removing redundant entries from student's foe list
        foes = [x for x in foes if x not in redundant_list]
        student = Student(student_id, student_name, pref_team_size, friends, foes)
        student_dict[student_id] = student
        student_name_to_id_map[student_name] = student_id
        student_id += 1
    return student_name_to_id_map


def read_input():
    """ Reads the command line arguments and store them in the global variables
    """
    global assn_grading, foe_complaint, friend_complaint
    file_path = sys.argv[1]
    assn_grading = int(sys.argv[2])
    foe_complaint = int(sys.argv[3])
    friend_complaint = int(sys.argv[4])
    student_name_to_id_map = parse_file(file_path)
    replace_student_name_with_id(student_name_to_id_map)


def print_input():
    """ Prints the input
    """
    global student_dict
    global assn_grading, size_complaint, foe_complaint, friend_complaint
    print 'Time required for grading assignment ->', assn_grading
    print 'Time required for complaining about team size ->', size_complaint
    print 'Time required for complaining about not teaming with friends ->', friend_complaint
    print 'Time required for complaining about teaming with foes ->', foe_complaint, '\n'
    for student in student_dict.values():
        print student


def find_compatibility_value(student1, student2):
    """ Calculates and returns the compatibility value between 2 students
    :param student1: Student object
    :param student2: Student object
    :return:         Compatibility value between 2 students
    """
    if student2.student_id in student1.friend_list:
        return 1
    elif student2.student_id in student1.foe_list:
        return -1
    else:
        return 0


def build_compatibility_matrix():
    """ Builds a N*N compatibility matrix for n students
        This matrix determines the compatibility between any 2 students
    :return: N*N compatibility matrix
    """
    global student_dict
    compatibility_matrix = [[0] * len(student_dict) for i in range(len(student_dict))]
    for i in range(len(student_dict)):
        for j in range(i + 1, len(student_dict)):
            val_1 = find_compatibility_value(student_dict[i], student_dict[j])
            val_2 = find_compatibility_value(student_dict[j], student_dict[i])
            compatibility_matrix[i][j] = compatibility_matrix[j][i] = val_1 + val_2
    return compatibility_matrix


def make_sd_list(compatibility_matrix):
    """ Finds standard deviation of all the students from their assigned compatibility values
    :param compatibility_matrix: N*N matrix that determines compatibility between any 2 students
    :return:                     List of tuples (std dev, student id) sorted by std dev in desc order
    """
    sd_list = list()
    for i in range(len(compatibility_matrix)):
        sd_list.append((numpy.std(compatibility_matrix[i]), i))
    return sorted(sd_list)


def initialize():
    """ We assume initial state where all the students are in separate teams
    :return: State object representing the initial state
    """
    student_to_team_map = dict()
    team_number = 0
    for student_id in student_dict:
        student_to_team_map[student_id] = team_number
        team_number += 1
    initial_state = State(student_to_team_map)
    return initial_state


def get_sw_state():
    """ Uses Squeaky Wheel algorithm to determine teams
        Reference: http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.521.2649&rep=rep1&type=pdf
    :return: State object representing the teams as outputted by the Squeaky Wheel algorithm
    """
    global student_dict, max_team_size
    initial_state = initialize()
    compatibility_matrix = build_compatibility_matrix()
    sd_list = make_sd_list(compatibility_matrix)
    curr_team_number = 0
    remaining_students = student_dict.keys()
    while remaining_students:
        squeakiest_student = student_dict[sd_list.pop()[1]]
        if squeakiest_student.student_id not in remaining_students:
            continue
        initial_state.assign_student_to_team(squeakiest_student.student_id, curr_team_number)
        remaining_students.remove(squeakiest_student.student_id)
        for i in range(1, max_team_size):
            best_team_member, best_cost = find_best_team_member(curr_team_number, remaining_students, initial_state)
            if best_cost < 0:
                initial_state.assign_student_to_team(best_team_member, curr_team_number)
                remaining_students.remove(best_team_member)
        curr_team_number += 1
    return State(initial_state.student_to_team_map)


def find_best_team_for_student(student_id, state):
    """ Finds the best team out of all the teams for a student
    :param student_id: ID of the student for whom a best team is to be determined
    :param state:      State object that contains the current configuration of the teams
    :return:           ID of the best team for the student
    """
    global student_dict, max_team_size
    team_set = state.team_to_student_map[state.student_to_team_map[student_id]]
    best_cost = student_dict[student_id].calculate_total_cost(team_set)
    best_team_num = state.student_to_team_map[student_id]
    for team_num, team in state.team_to_student_map.iteritems():
        if team_num != state.student_to_team_map[student_id] and \
                        len(state.team_to_student_map[team_num]) < max_team_size:
            curr_cost = state.cost_of_placing_student_in_team(student_id, team_num)
            if curr_cost < best_cost:
                best_cost = curr_cost
                best_team_num = team_num
    return best_team_num


def find_best_team_member(team_num, candidates, state):
    """ Finds the best team member out of a given list of candidates for a team
        Best team member is one that results in the lowest cost
    :param team_num:   Team number for which the best team member is to be determined
    :param candidates: List of students that could be added to the team
    :param state:      State object that contains the current configuration of the teams
    :return:           ID of the best team member, Cost of keeping the student in the team
    """
    best_cost = sys.maxint
    best_team_member = -1
    for candidate in candidates:
        curr_cost = state.cost_of_placing_student_in_team(candidate, team_num)
        if curr_cost < best_cost:
            best_cost = curr_cost
            best_team_member = candidate
    return best_team_member, best_cost


def find_next_state(curr_state):
    """ Takes the current state (configuration of students to teams) and finds the next state
    :param curr_state: State object representing the current configuration of students to teams
    :return:           State object representing the next configuration of students to teams
    """
    global tabu_dict
    while curr_state.student_cost_queue.qsize() > 0:
        student_id = curr_state.student_cost_queue.get()[1]
        if student_id not in tabu_dict:
            best_team_num = find_best_team_for_student(student_id, curr_state)
            curr_state.assign_student_to_team(student_id, best_team_num)
            tabu_dict[student_id] = 1
            break
    student_to_team_map = curr_state.student_to_team_map
    to_be_removed_list = list()
    for student_id, tabu_val in tabu_dict.iteritems():
        if tabu_val < 5:
            tabu_dict[student_id] = tabu_val + 1
        else:
            to_be_removed_list.append(student_id)
    for student_id in to_be_removed_list:
        tabu_dict.pop(student_id)
    return State(student_to_team_map)


def find_best_state():
    """ Determines and returns the best state
        Best state is one that results in the least cost
    :return: The best state
    """
    global threshold_iterations
    curr_state = best_state = get_sw_state()
    counter = 0
    # Checking whether the best state is changed in the last 'threshold_iterations' iterations
    # Borrowed from: http://ieeexplore.ieee.org/document/5518761/
    while counter < threshold_iterations:
        next_state = find_next_state(curr_state)
        if next_state.total_cost < best_state.total_cost:
            best_state = next_state
            counter = 0
        curr_state = next_state
        counter += 1
    return best_state


def main():
    """ Main function
    """
    read_input()
    # print_input()
    # print 'Printing best state'
    print find_best_state()


if __name__ == '__main__':
    main()
