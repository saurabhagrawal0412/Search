import sys
from Queue import PriorityQueue
from collections import defaultdict

student_dict = dict()
assn_grading = 0
size_complaint = 1
friend_complaint = 0
foe_complaint = 0
best_state = None


class Student:
    def __init__(self, student_name, pref_team_size, friend_list, foe_list):
        self.student_name = student_name
        self.pref_team_size = pref_team_size
        self.friend_list = friend_list
        self.foe_list = foe_list
        self.student_to_team_map = dict()
        self.team_to_student_map = defaultdict(set)

    def __str__(self):
        curr_str = 'Student name = ' + self.student_name + '\n'
        curr_str = curr_str + 'Preferred team size = ' + str(self.pref_team_size) + '\n'
        curr_str = curr_str + 'Friends = ' + str(self.friend_list) + '\n'
        curr_str = curr_str + 'Foes = ' + str(self.foe_list)
        return curr_str

    def calculate_costs(self, team):
        global size_complaint, friend_complaint, foe_complaint
        curr_size_complaint = 0
        curr_friend_complaint = 0
        curr_foe_complaint = 0
        if self.pref_team_size != len(team):
            curr_size_complaint = size_complaint
        for friend in self.friend_list:
            if friend not in team:
                curr_friend_complaint = curr_friend_complaint + friend_complaint
        for foe in self.foe_list:
            if foe in team:
                curr_foe_complaint = curr_foe_complaint + foe_complaint
        return curr_size_complaint, curr_friend_complaint, curr_foe_complaint


class State:
    def __init__(self, student_to_team_map):
        global assn_grading
        self.student_to_team_map = student_to_team_map
        self.team_to_student_map = self.get_team_to_student_map()
        self.assn_grading_cost = assn_grading * len(self.team_to_student_map)
        self.friend_cost_queue = PriorityQueue()
        self.foe_cost_queue = PriorityQueue()
        self.team_size_cost_queue = PriorityQueue()
        self.total_cost = self.assn_grading_cost
        self.calculate_costs_for_all()

    def calculate_costs_for_all(self):
        global student_dict
        for student_name, team_number in self.student_to_team_map.iteritems():
            team = self.team_to_student_map[team_number]
            student = student_dict[student_name]
            curr_size_complaint, curr_friend_complaint, curr_foe_complaint = student.calculate_costs(team)
            self.total_cost += curr_size_complaint + curr_friend_complaint + curr_foe_complaint
            # print 'Student ->', student
            # print 'Size complaint ->', curr_size_complaint
            # print 'Friend complaint ->', curr_friend_complaint
            # print 'Foe complaint ->', curr_foe_complaint
            # print ''
            self.team_size_cost_queue.put((curr_size_complaint, student_name))
            self.friend_cost_queue.put((curr_friend_complaint, student_name))
            self.foe_cost_queue.put((curr_foe_complaint, student_name))
            # print 'Printing size queue'
            # self.print_queue(self.team_size_cost_queue)
            # print 'Printing friend queue'
            # self.print_queue(self.friend_cost_queue)
            # print 'Printing foe queue'
            # self.print_queue(self.foe_cost_queue)

    def __str__(self):
        state_str = ''
        for team_number, team_set in self.team_to_student_map.iteritems():
            state_str += '[ ' + ', '.join(team_set) + ' ]' + '\n'
        state_str += 'Total cost -> ' + str(self.total_cost) + '\n'
        return state_str

    def print_queue(self, queue_to_print):
        for i in range(0, queue_to_print.qsize()):
            print queue_to_print.queue[i]

    def get_team_to_student_map(self):
        team_to_student_map = defaultdict(set)
        for student_name in self.student_to_team_map:
            team_number = self.student_to_team_map[student_name]
            team_to_student_map[team_number].add(student_name)
        return team_to_student_map

    def get_student_team(self, student_name):
        team_num = self.student_to_team_map[student_name]
        team = self.team_to_student_map[team_num]
        return team

    def cost_of_placing_student_in_team(self, student_name, team_number):
        global student_dict
        global friend_complaint, foe_complaint, size_complaint, assn_grading
        student = student_dict[student_name]
        team = self.team_to_student_map[team_number]
        curr_team_size = len(team)
        curr_assn_grading = 0 if curr_team_size > 1 else assn_grading
        if student.pref_team_size == 0 or curr_team_size == student.pref_team_size + 1:
            team_size_complaints = size_complaint
        else:
            team_size_complaints = 0
        friend_count_in_team = len(list(team.intersection(student.friend_list)))
        foes_count_in_team = len(list(team.intersection(student.foe_list)))
        for team_member_name in team:
            team_member = student_dict[team_member_name]
            if team_member.pref_team_size == curr_team_size + 1:
                team_size_complaints += 1
            if student.student_name in team_member.friend_list:
                friend_count_in_team += 1
            elif student.student_name in team_member.foe_list:
                foes_count_in_team += 1
        total_cost = (team_size_complaints * size_complaint) + (foes_count_in_team * foe_complaint) - \
                     (friend_count_in_team * friend_complaint) - curr_assn_grading

        # print 'Student ->', student_name
        # print 'New team ->', team
        # print 'Total cost ->', total_cost
        return total_cost


def find_best_team_for_student(student_name, state):
    best_cost = sys.maxint
    best_team_num = 0
    # print 'Inside find_best_team_for_student:', student_name
    for team_num, team in state.team_to_student_map.iteritems():
        if team_num != state.student_to_team_map[student_name]:
            curr_cost = state.cost_of_placing_student_in_team(student_name, team_num)
            if curr_cost < best_cost:
                best_cost = curr_cost
                best_team_num = team_num
    # print 'Best team num for student: ', best_team_num
    return best_team_num


def initialize():
    student_to_team_map = dict()
    team_number = 1
    for student_name in student_dict:
        student_to_team_map[student_name] = team_number
        team_number += 1
    initial_state = State(student_to_team_map)
    return initial_state


def print_dict():
    global student_dict
    for student_name in student_dict:
        print student_dict[student_name]


def print_input():
    global assn_grading, size_complaint, foe_complaint, friend_complaint
    print 'Time required for grading assignment ->', assn_grading
    print 'Time required for complaining about team size ->', size_complaint
    print 'Time required for complaining about not teaming with friends ->', friend_complaint
    print 'Time required for complaining about teaming with foes ->', foe_complaint, '\n'
    print_dict()


def parse_file(file_path):
    global student_dict
    fh = open(file_path, 'r')
    lines = fh.read().splitlines()
    fh.close()
    for line in lines:
        fields = line.split(' ')
        student_name = fields[0]
        pref_team_size = int(fields[1])
        friends = fields[2].split(',') if fields[2] != '_' else []
        foes = fields[3].split(',') if fields[3] != '_' else []
        student = Student(student_name, pref_team_size, friends, foes)
        student_dict[student_name] = student


def read_input():
    global assn_grading, foe_complaint, friend_complaint
    file_path = sys.argv[1]
    assn_grading = int(sys.argv[2])
    foe_complaint = int(sys.argv[3])
    friend_complaint = int(sys.argv[4])
    parse_file(file_path)


def find_next_state(curr_state):
    max_friend_cost = curr_state.friend_cost_queue.queue[0]
    # print 'max_friend_cost ->', max_friend_cost
    max_foe_cost = curr_state.foe_cost_queue.queue[0]
    # print 'max_foe_cost ->', max_foe_cost
    max_team_size_cost = curr_state.team_size_cost_queue.queue[0]
    # print 'max_team_size_cost ->', max_team_size_cost
    max_overall_cost = max(max_friend_cost, max_foe_cost, max_team_size_cost)
    # print 'max_overall_cost ->', max_overall_cost
    student_name = max_overall_cost[1]
    best_team = find_best_team_for_student(student_name, curr_state)
    student_to_team_map = curr_state.student_to_team_map
    student_to_team_map[student_name] = best_team
    return State(student_to_team_map)


def main():
    global best_state
    read_input()
    print_input()
    curr_state = initialize()
    best_state = curr_state
    print curr_state

    for i in range(0, 300):
        print 'Printing current state\n', curr_state
        next_state = find_next_state(curr_state)
        if next_state.total_cost < best_state.total_cost:
            best_state = next_state
        curr_state = next_state
    print '\nPrinting best state\n'
    print best_state


if __name__ == '__main__':
    main()
