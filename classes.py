from numpy import random
from math import floor
from numpy import bincount, unique
from scipy.stats import binom

# from random import choice


class one_arm_bandit:
    def __init__(self):
        self.seed = random.rand()


class many_bandits:
    def __init__(self, n=3):
        self.n = n
        self.mab = []
        self.make_bandits()

    def make_bandits(self):
        for i in range(0, self.n):
            self.mab.append(one_arm_bandit().seed)
        return self.mab


def test_machine(arm):
    pull = random.rand()
    # print("Pull: ", pull, " Arm: ", arm)
    if pull >= arm:
        return 1
    else:
        return 0


def pull_arm(r, pa):
    arm_pulled = r[pa]
    return test_machine(arm_pulled)


def brute_force(r, n_tests=10000):
    arms_picked = []
    num_r = r.__len__()
    interval = 1 / num_r
    for i in range(0, n_tests):
        arm_result = pull_arm(r, random.choice(interval))
        arms_picked.append(arm_result)
    return arms_picked

def bias_setter():
    bias_check_1 = 0
    return bias_check_1

class arm_tracker:
    def __init__(self, num_bands=3, n_tests=10000, bias_check_1 = 0):
        self.n_tests = n_tests
        self.num_bands = num_bands
        self.row = many_bandits(self.num_bands).mab

        self.num_r = self.row.__len__()
        self.interval = 1 / self.num_r
        self.arms_picked = []
        self.bias_check_1 = 0
        self.bias_check_2 = 0
        self.test_results_prob_lead = self.build_states_prob_lead()
        self.test_results_random = self.build_stats_random()
        self.odds = self.find_odds()



    # self.state_tracker = self.track_state()



    def find_odds(self):
        odds = []
        for i in range(0, self.num_bands):
            odds.append(1 - self.row[i])
        return odds

    def build_stats_random(self):
        self.tracker = []
        for i in range(0, self.num_bands):
            self.tracker.append([])
        for i in range(0, 3*self.n_tests):
            self.pick_any_random_arm()
        return self.check_test_results()

    def pick_any_random_arm(self):
        arm_index = [i for i in range(len(self.row))]
        pa = random.choice(arm_index)
        arm_result = pull_arm(self.row, pa)
        self.tracker[pa].append(arm_result)

    def check_test_results(self):
        test_results = []
        for i in range(0, self.tracker.__len__()):
            if sum(bincount(self.tracker[i])) == 0:
                # print("No tests performed on arm #", i)
                test_results.append(-1)
            elif unique(self.tracker[i]).__len__() == 1:
                # print("Insufficient statistics to estimate odds on arm #", i)
                if self.tracker[i].__len__() > 3:
                    test_results.append(sum(self.tracker[i]) / self.tracker[i].__len__())
                else:
                    test_results.append(-2)
            else:
                test_results.append(bincount(self.tracker[i])[1] / sum(bincount(self.tracker[i])))
        return test_results

    def build_states_prob_lead(self):
        self.tracker = []
        print("The status of tracker in prob_lead before instantiation: ", self.tracker.__len__())
        for i in range(0, self.num_bands):
            self.tracker.append([])
        print("The status of tracker in prob_lead after instantiation: ", self.tracker.__len__())
        for n in range(0, self.n_tests):
            track_state_1, track_state_2 = self.track_state()
            # print(track_state_1)
            if all(st == 0 for st in track_state_2):
                self.pick_any_random_arm()
            elif any(st != 0 for st in track_state_2):
                if (self.bias_check_1 % 2) == 0:
                    self.set_of_arms_pull("prob_lead", "known", track_state_1)
                else:
                    self.set_of_arms_pull("prob_lead", "unknown", track_state_1)

        return self.check_test_results()

    def set_of_arms_pull(self, decision_type, k_or_u, track_state):
        known_arms = [i for i in range(len(track_state)) if track_state[i] > 0]  # Identify index for known
        unknown_arms = [i for i in range(len(track_state)) if track_state[i] == 0]  # Identify index for unknown
        if decision_type == "random": # This 'random' flag is redundant for normal operation but useful for debugging this
            # function
            if k_or_u == "unknown" and unknown_arms.__len__() != 0:
                choose_arm = random.choice(unknown_arms)
            else:
                choose_arm = random.choice(known_arms)
            arm_result = pull_arm(self.row, choose_arm)
            self.tracker[choose_arm].append(arm_result)
            self.bias_check_1 += 1
            return self.bias_check_1
        elif decision_type == "prob_lead":
            if k_or_u == "unknown" and unknown_arms.__len__() != 0:
                for i in range(3): # FIXME: This isn't working as expected; none of the self.trackers are pulling 3 arms
                    choose_arm = random.choice(unknown_arms)
                    arm_result = pull_arm(self.row, choose_arm)
                    self.tracker[choose_arm].append(arm_result)
            else:

                ongoing_test_results = self.check_test_results()
                well_tracked_arms = [i for i in range(len(ongoing_test_results)) if ongoing_test_results[i] > 0.0]
                if (self.bias_check_2 % 2) == 0:
                    if well_tracked_arms.__len__() >= 3: # TODO: "The 3 or more experiments could be a variable we play with"
                        for i in range(3):
                            choose_arm = ongoing_test_results.index(sorted([ongoing_test_results[i] for i in well_tracked_arms], reverse=True)[i])
                            arm_result = pull_arm(self.row, choose_arm)
                            self.tracker[choose_arm].append(arm_result)
                        # TODO: I also need to set the "batch_pulls = True" self-flag and make sure it doesn't mess up with the unknown-known-wellknown cycle of arm-pulls. This cycle is probably a critical piece of optimization.
                        # TODO: Start tracking some sort of metric to compare this new selection process vs. random sampling

                    else:
                        for i in range(3):
                            choose_arm = random.choice(known_arms)
                            arm_result = pull_arm(self.row, choose_arm)
                            self.tracker[choose_arm].append(arm_result)
                else:
                    if known_arms.__len__() != well_tracked_arms.__len__():
                        for i in range(3):
                            choose_arm = random.choice([item for item in known_arms if item not in well_tracked_arms])
                            arm_result = pull_arm(self.row, choose_arm)
                            self.tracker[choose_arm].append(arm_result)
                    else:
                        for i in range(3):
                            choose_arm = random.choice(known_arms)
                            arm_result = pull_arm(self.row, choose_arm)
                            self.tracker[choose_arm].append(arm_result)
            self.bias_check_2 += 1
            self.bias_check_1 += 1
            return



    def track_state(self):
        track_state_1 = []
        track_state_2 = []
        for i in range(0, self.tracker.__len__()):
            if self.tracker[i].__len__() == 0:  # Check if that arm has been pulled at all and there's a result
                track_state_1.append(0)  # State 1: If nothing has been pulled, be 0
                track_state_2.append(0)  # State 2: If nothing has been pulled, be 0
            else:
                track_state_1.append(1)  # State 1: If something has been pulled, be that something
                if unique(self.tracker[i]).__len__() == 1:
                    track_state_2.append(0)  # State 2: if there's only 1 result, be 0
                else:
                    track_state_2.append(1)  # State 2: if there's more than 1 result, be 1
        return track_state_1, track_state_2
