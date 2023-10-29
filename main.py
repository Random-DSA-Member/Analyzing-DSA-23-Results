import os
import csv
from collections import defaultdict

FOLDER_NAME = "processed"
NAME = 0 # Indexes
CHAPTER = 1
DID_VOTE = 2
VOTE = 3

YES = "Yes"
NO = "No"
ABSTAIN = "Abstain"
DID_NOT_VOTE = "Did Not Vote"
        
def get_vote_result(row):
    if row[DID_VOTE] == NO:
        return DID_NOT_VOTE
    return row[VOTE]

class VoteResult:
    def __init__(self):
        self.result = defaultdict(lambda: 0)

    def add_vote(self, vote):
        self.result[vote] += 1

    def num_delegates(self):
        delegates = 0
        for vote in self.result:
            delegates += self.result[vote]
        return delegates

    def any_votes(self):
        return self.result[YES]+self.result[NO] > 0
        
    def percentage(self):
        yes_votes = self.result[YES]
        total_votes = self.result[YES]+self.result[NO]
        return yes_votes/total_votes*100

    # 0% yes -> 100% united | 50% yes -> 0% united | 100% yes -> 100% united
    def unity(self):
        return 2*abs(self.percentage()-50)

    def __str__(self):
        if not self.any_votes():
            return "No votes"
        yes_votes = self.result[YES]
        total_votes = self.result[YES]+self.result[NO]
        return f"{yes_votes}/{total_votes} -- {self.percentage():.2f}% yes, unity score: {self.unity():.2f}"

class VoteResultMap:
    def __init__(self, vote_map):
        self.vote_map = vote_map
        # self.filenames should be the keys of vote_map,
        # but in an ordered list to ensure a consistent order
        self.filenames = list(vote_map.keys())
        self.filenames.sort()

    def num_delegates(self):
        return self.vote_map[self.filenames[0]].num_delegates()

    def any_votes(self):
        for filename in self.filenames:
            if self.vote_map[filename].any_votes():
                return True
        return False

    def average_unity(self):
        sum_unity_scores = 0
        num_valid_votes = 0
        for filename in self.filenames:
            if self.vote_map[filename].any_votes():
                sum_unity_scores += self.vote_map[filename].unity()
                num_valid_votes += 1
        if num_valid_votes == 0:
            return 0
        return sum_unity_scores / num_valid_votes

    def __str__(self):
        lines = []
        for filename in self.filenames:
            lines.append(f"{filename}: {self.vote_map[filename]}")
        lines.append(f"Average Unity Score: {self.average_unity():.2f}")
        return "\n".join(lines)
    
class AllVoteData:
    def __init__(self, all_data):
        self.data = all_data
        # self.filenames should be the keys of all_data,
        # but in an ordered list to ensure a consistent order
        self.filenames = list(all_data.keys())
        self.filenames.sort()

        # Precompute list of chapters:
        chapter_set = set()
        for filename in self.filenames:
            for row in self.data[filename]:
                chapter_set.add(row[CHAPTER])
        self.chapters = list(chapter_set)
        self.chapters.sort()

    def get_result(self, filename):
        vote_result = VoteResult()
        for row in self.data[filename]:
            vote_result.add_vote(get_vote_result(row))
        return vote_result

    def get_chapter_result(self, filename, chapter):
        vote_result = VoteResult()
        for row in self.data[filename]:
            if row[CHAPTER] == chapter:
                vote_result.add_vote(get_vote_result(row))
        return vote_result

    def get_all_results(self):
        vote_map = {}
        for filename in self.filenames:
            vote_map[filename] = self.get_result(filename)
        return VoteResultMap(vote_map)

    def get_all_chapter_results(self, chapter):
        vote_map = {}
        for filename in self.filenames:
            vote_map[filename] = self.get_chapter_result(filename, chapter)
        return VoteResultMap(vote_map)

    def get_all_chapter_results_for_all_chapters(self):
        chapter_result_map = {}
        for chapter in self.chapters:
            chapter_result_map[chapter] = self.get_all_chapter_results(chapter)
        chapter_result_map["EVERYONE"] = self.get_all_results()
        return chapter_result_map

    def print_chapters_by_average_unity(self, min_delegates=0):
        all_results = self.get_all_chapter_results_for_all_chapters()
        unity_chapter_pairs = []
        for chapter in all_results:
            unity_chapter_pairs.append((chapter, all_results[chapter].average_unity()))
        unity_chapter_pairs.sort(key=lambda pr: pr[1], reverse=True)
        for chapter, unity in unity_chapter_pairs:
            num_delegates = all_results[chapter].num_delegates()
            if num_delegates < min_delegates:
                continue
            if not all_results[chapter].any_votes():
                print(f"{chapter} had no votes")
            else:
                print(f"{chapter} | Unity: {unity:.2f} with {num_delegates} Delegates")

def gendata():
    all_data = {}
    filenames = os.listdir(FOLDER_NAME)
    for filename in filenames:
        all_data[filename] = []
        with open(f"{FOLDER_NAME}/{filename}") as file:
            reader = csv.reader(file)

            first_row = True
            for row in reader:
                if first_row: # Skip header row
                    first_row = False
                else:
                    all_data[filename].append(row)
                    assert(len(row) == 5) # We expect five columns in each row!
    return AllVoteData(all_data)

if __name__ == "__main__":
    # Analyze the votes from a specific chapter:
    # print(gendata().get_all_chapter_results("San Francisco"))
    gendata().print_chapters_by_average_unity(min_delegates=5)
