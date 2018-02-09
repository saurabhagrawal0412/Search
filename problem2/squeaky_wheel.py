from collections import defaultdict
import sys
import numpy

student_dict = dict()
assn_grading = 0
size_complaint = 1
friend_complaint = 0
foe_complaint = 0
student_to_team_map = dict()
team_to_student_map = defaultdict(set)
max_team_size = 3


class Student:
    def __init__(self, student_id, student_name, pref_team_size, friend_list, foe_list):
        self.student_id = student_id
        self.student_name = student_name
        self.pref_team_size = pref_team_size
        self.friend_list = friend_list
        self.foe_list = foe_list

    def __str__(self):
        curr_str = 'Student ID = ' + str(self.student_id) + '\n'
        curr_str += 'Student name = ' + self.student_name + '\n'
        curr_str += 'Preferred team size = ' + str(self.pref_team_size) + '\n'
        curr_str += 'Friends = ' + str(self.friend_list) + '\n'
        curr_str += 'Foes = ' + str(self.foe_list) + '\n'
        return curr_str

    def calculate_total_cost(self, team):
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
        total_cost = curr_size_complaint + curr_friend_complaint + curr_foe_complaint
        return total_cost


def parse_file(file_path):
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
        friends = fields[2].split(',') if fields[2] != '_' else []
        foes = fields[3].split(',') if fields[3] != '_' else []
        student = Student(student_id, student_name, pref_team_size, friends, foes)
        student_dict[student_id] = student
        student_name_to_id_map[student_name] = student_id
        student_id += 1
    return student_name_to_id_map


def replace_student_name_with_id(student_name_to_id_map):
    global student_dict
    # print 'student_name_to_id_map ->', student_name_to_id_map
    for student in student_dict.values():
        new_friend_list = list()
        for friend_name in student.friend_list:
            new_friend_list.append(student_name_to_id_map[friend_name])
        student.friend_list = new_friend_list
        new_foe_list = list()
        for foe_name in student.foe_list:
            new_foe_list.append(student_name_to_id_map[foe_name])
        student.foe_list = new_foe_list


def read_input():
    global assn_grading, foe_complaint, friend_complaint
    file_path = sys.argv[1]
    assn_grading = int(sys.argv[2])
    foe_complaint = int(sys.argv[3])
    friend_complaint = int(sys.argv[4])
    student_name_to_id_map = parse_file(file_path)
    replace_student_name_with_id(student_name_to_id_map)


def print_dict():
    global student_dict
    for student in student_dict.values():
        print student


def print_input():
    global assn_grading, size_complaint, foe_complaint, friend_complaint
    print 'Time required for grading assignment ->', assn_grading
    print 'Time required for complaining about team size ->', size_complaint
    print 'Time required for complaining about not teaming with friends ->', friend_complaint
    print 'Time required for complaining about teaming with foes ->', foe_complaint, '\n'
    print_dict()


def find_compatibility_value(student1, student2):
    if student2.student_id in student1.friend_list:
        return 1
    elif student2.student_id in student1.foe_list:
        return -1
    else:
        return 0


def fill_compatibility_matrix():
    global student_dict
    compatibility_matrix = [[0] * len(student_dict) for i in range(len(student_dict))]
    for i in range(len(student_dict)):
        for j in range(i + 1, len(student_dict)):
            val_1 = find_compatibility_value(student_dict[i], student_dict[j])
            val_2 = find_compatibility_value(student_dict[j], student_dict[i])
            compatibility_matrix[i][j] = compatibility_matrix[j][i] = val_1 + val_2
    return compatibility_matrix


def make_sd_list(compatibility_matrix):
    sd_list = list()
    for i in range(len(compatibility_matrix)):
        sd_list.append((numpy.std(compatibility_matrix[i]), i))
    return sorted(sd_list)


def cost_of_placing_student_in_team(student_num, team_num):
    global student_dict, team_to_student_map
    global friend_complaint, foe_complaint, size_complaint, assn_grading
    student = student_dict[student_num]
    team = team_to_student_map[team_num]
    curr_team_size = len(team)
    curr_assn_grading = 0 if curr_team_size > 1 else assn_grading
    team_size_complaints = 0 if student.pref_team_size == 0 or curr_team_size + 1 == student.pref_team_size else 1
    friend_count_in_team = len(list(team.intersection(student.friend_list)))
    foes_count_in_team = len(list(team.intersection(student.foe_list)))
    for team_member_name in team:
        team_member = student_dict[team_member_name]
        if team_member.pref_team_size != curr_team_size + 1:
            team_size_complaints += 1
        if student.student_name in team_member.friend_list:
            friend_count_in_team += 1
        elif student.student_name in team_member.foe_list:
            foes_count_in_team += 1
    total_cost = (team_size_complaints * size_complaint) + (foes_count_in_team * foe_complaint) - \
                 (friend_count_in_team * friend_complaint) - curr_assn_grading
    return total_cost


def find_best_team_for_student(student_id):
    global student_dict, student_to_team_map, team_to_student_map
    student_team_set = team_to_student_map[student_to_team_map[student_id]]
    best_cost = student_dict[student_id].calculate_total_cost(student_team_set)
    best_team_num = 0
    # print 'Inside find_best_team_for_student:', student_name
    for team_num, team in team_to_student_map.iteritems():
        if team_num != student_to_team_map[student_id]:
            curr_cost = cost_of_placing_student_in_team(student_id, team_num)
            if curr_cost < best_cost:
                best_cost = curr_cost
                best_team_num = team_num
    # print 'Best team num for student: ', best_team_num
    return best_team_num


def find_best_team_member(team_num, candidates):
    best_cost = sys.maxint
    best_team_member = -1
    for candidate in candidates:
        curr_cost = cost_of_placing_student_in_team(candidate, team_num)
        if curr_cost < best_cost:
            best_cost = curr_cost
            best_team_member = candidate
    return best_team_member, best_cost


def assign_student_to_team(student_id, team_num):
    global student_to_team_map, team_to_student_map
    if student_id in student_to_team_map:
        curr_team_num = student_to_team_map[student_id]
        team_to_student_map[curr_team_num].remove(student_id)
    student_to_team_map[student_id] = team_num
    team_to_student_map[team_num].add(student_id)


def find_sw_teams(sd_list):
    global student_dict, max_team_size
    curr_team_number = 0
    remaining_students = student_dict.keys()
    while remaining_students:
        squeakiest_student = student_dict[sd_list.pop()[1]]
        print 'squeakiest_student ->', squeakiest_student.student_name
        if squeakiest_student.student_id not in remaining_students:
            continue
        assign_student_to_team(squeakiest_student.student_id, curr_team_number)
        remaining_students.remove(squeakiest_student.student_id)
        for i in range(1, max_team_size):
            best_team_member, best_cost = find_best_team_member(curr_team_number, remaining_students)
            print 'best_team_member ->', best_team_member
            print 'best_cost ->', best_cost
            if best_cost < 0:
                assign_student_to_team(best_team_member, curr_team_number)
                remaining_students.remove(best_team_member)
        curr_team_number += 1


def print_teams():
    global team_to_student_map, student_dict
    for team in team_to_student_map.values():
        team_str = ''
        for teammate_num in team:
            teammate = student_dict[teammate_num]
            team_str += (teammate.student_name + ' ')
        print team_str
    print 'Total cost ->', calculate_costs_for_all()


def calculate_costs_for_all():
    global student_dict, student_to_team_map, team_to_student_map, assn_grading
    total_cost = len(team_to_student_map) * assn_grading
    for student_name, team_number in student_to_team_map.iteritems():
        team = team_to_student_map[team_number]
        student = student_dict[student_name]
        total_cost += student.calculate_total_cost(team)
    return total_cost


def main():
    read_input()
    print_input()
    compatibility_matrix = fill_compatibility_matrix()
    sd_list = make_sd_list(compatibility_matrix)
    find_sw_teams(sd_list)
    print_teams()


if __name__ == '__main__':
    main()
