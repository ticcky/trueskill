#!/usr/bin/env python
#
# author: Lukas Zilka
#
from collections import defaultdict

class Gauss:
    def __init__(self, mean=0.0, variance=0.0):
        self.mean = mean
        self.variance = variance

    def set(self, gauss):
        self.mean = gauss.mean
        self.variance = gauss.variance

    def convolve(self, *gausses):
        for gauss in gausses:
            self.mean += gauss.mean
            self.variance += gauss.variance

    def __neg__(self):
        return Gauss(mean=-self.mean, variance=self.variance)

    def __div__(self, div):
        new_variance = 1 / (1 / self.variance + 1 / div.variance)
        new_mean = new_variance * (self.mean / self.variance + div.mean / div.variance)
        return Gauss(mean=new_mean, variance=new_variance)

    def __str__(self):
        return "%.2f (+-%.2f)" % (self.mean, self.variance, )


class Game(object):
    def __init__(self, outcome, team_assignment, trueskill):
        self.trueskill = trueskill
        self.outcome = outcome
        self.team_assignment = defaultdict(set)
        for pid, team in enumerate(team_assignment):
            self.team_assignment[team].add(pid)

        self.p_cnt = p_cnt = trueskill.players_cnt
        self.t_cnt = t_cnt = len(set(team_assignment))

        self.msg_fskill_skill = {}
        self.msg_fperf_perf = {}
        for player_id in range(p_cnt):
            self.msg_fskill_skill[player_id] = Gauss()
            self.msg_fperf_perf[player_id] = Gauss()

        self.msg_fteam_team = {}
        for team_id in range(t_cnt):
            self.msg_fteam_team[team_id] = Gauss()


        self.msg_fdiff_diff = {}
        self.msg_fres_diff = {}
        self.msg_fdiff_next = {}
        self.msg_fdiff_prev = {}
        for diff in range(t_cnt - 1):
            self.msg_fdiff_diff[diff] = Gauss()
            self.msg_fres_diff[diff] = Gauss()
            self.msg_fdiff_next[diff] = Gauss()
            self.msg_fdiff_prev[diff] = Gauss()





    def infer_skill(self):
        # run scenario
        self.update_skill()
        self.update_perf()
        self.update_team()

        for diff in range(self.t_cnt - 1):
            self.update_diff(diff, diff > 0, diff < self.t_cnt - 1)

    def update_skill(self):
        for pid in range(self.p_cnt):
            self.msg_fskill_skill[pid].set(self.trueskill.skill0)

    def update_perf(self):
        for pid in range(self.p_cnt):
            self.msg_fperf_perf[pid].convolve(self.msg_fskill_skill[pid])

    def update_team(self):
        for tid in range(self.t_cnt):
            perfs = list(self.msg_fperf_perf[pid] for pid in self.team_assignment[tid])
            self.msg_fteam_team[tid].convolve(*perfs)
            print 'team', tid, self.msg_fteam_team[tid]

    def update_diff(self, diff, left=True, right=True):
        # diff factor -> diff
        self.msg_fdiff_diff[diff].convolve(self.msg_fteam_team[diff], -self.msg_fteam_team[diff + 1])

        # diff result factor -> diff
        self.msg_fres_diff[diff] = self.compute_diff_res(diff) / self.msg_fdiff_diff[diff]

        self.msg_fdiff_next[diff].convolve(self.msg_fteam_team[diff], self.msg_fres_diff[diff])

        print 'diff', diff, self.msg_fdiff_next[diff]


    def compute_diff_res(self, diff):
        outcome = self.outcome[diff] - self.outcome[diff + 1]
        margin = self.trueskill.diff_margin

        def delta(x):
            return lmbd(x) * (lmbd(x) - x)

        def lmbd(x):
            return std_norm(x) / (1 - std_norm_cummul(x))

        def std_norm_cummul(x):
            #TODO
            return 0.5

        def std_norm(x):
            #TODO
            return x

        if outcome == 0:  # tie
            beta = (margin - self.msg_fdiff_diff[diff].mean) / self.msg_fdiff_diff[diff].variance
            new_mean = self.msg_fdiff_diff[diff].mean - self.msg_fdiff_diff[diff].variance * std_norm(beta) / std_norm_cummul(beta)
            new_variance = self.msg_fdiff_diff[diff].variance**2 * (1 - beta * std_norm(beta) / std_norm_cummul(beta) - (std_norm(beta) / std_norm_cummul(beta))**2)
        else:  # win
            alpha = (margin - self.msg_fdiff_diff[diff].mean) / self.msg_fdiff_diff[diff].variance
            new_mean = self.msg_fdiff_diff[diff].mean + self.msg_fdiff_diff[diff].variance * lmbd(alpha)

            new_variance = self.msg_fdiff_diff[diff].variance**2
            new_variance *= 1 - delta(alpha)

        res = Gauss(mean=new_mean, variance=new_variance)

        return res









    def get_new_skill(self):
        return 0.0, 0.0



class TrueSkill(object):
    def __init__(self):
        self.players_cnt = 0

        self.skill = []

        self.skill0 = Gauss(mean=5.0, variance=1.0)
        self.diff_margin = 0.1


    def new_player(self):
        player_id = self.players_cnt
        self.players_cnt += 1

        return player_id

    def report_game(self, team_assignment, outcome):
        game = Game(outcome, team_assignment, self)
        game.infer_skill()

        self.skill_mean, self.skill_variance = game.get_new_skill()



def main():
    ts = TrueSkill()
    ts.new_player()
    ts.new_player()
    ts.new_player()
    ts.new_player()
    ts.report_game([0, 1, 1, 2], [0, 1, 1])

if __name__ == '__main__':
    main()