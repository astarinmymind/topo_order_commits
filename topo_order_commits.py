#!/usr/bin/python3

import os, sys
from collections import deque


class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()


"""
This function is used to find the .git directory that is present in the current directory or any of its parent directories.
If no .git directory is found, the program exits with an error message.
"""


def getPath():
    # get current working directory
    current = os.getcwd()
    # returns true if path is an existing directory
    is_valid_path = False

    while current != "":
        # append .git
        check = current + "/.git"

        # check if path is valid
        is_valid_path = os.path.isdir(check)

        # if valid, return
        if is_valid_path:
            return current
        # else, delete
        else:
            current = current[: current.rfind("/")]

    # .git not found, print to stderr
    print("Not inside a Git repository", file=sys.stderr)
    exit(1)


"""
This function navigates to the .git/refs/heads directory to get the list of local branch names and their corresponding commit hashes. 
The information is returned as a dictionary with branch names as keys and commit hashes as values.
"""


def getBranch():
    path = getPath() + "/.git/refs/heads"
    branches = dict()

    for root, dirs, files in os.walk(path):
        for f in files:
            branch = root + "/" + f
            head = branch[branch.rfind("heads/") + 6 :]
            commit = (open(branch).read()).strip()
            branches[head] = commit

    return branches


"""
This function creates a mapping of commit hashes to their corresponding branch names, using the information retrieved by getBranch()
"""


# returns dictionary where branch name outputted when given commit hash
def map_hash_to_branch():
    branch = getBranch()
    hash_to_branch = dict()  # maps hash to branch name
    for b, commit in branch.items():
        hash_to_branch[commit] = b
    return hash_to_branch


"""
This function builds the commit graph. 
For each branch, it starts from the latest commit and traverses the commit history by following the parent commits. 
The commits and their relationships are stored in CommitNode objects and added to the graph dictionary (commit hash to CommitNode mapping). 
The function also identifies root commits (those without parents) and returns the graph and the set of root commits.
"""


def getGraph():
    # branch
    branch = getBranch()

    # dictionary
    graph = dict()  # maps hash to commitnode object
    stack = []
    root_commits = set()

    # traverse commit history by following parents of the head
    # create a commitnode object for each new commit seen
    # populate commitnode with parents
    for b, commit in branch.items():
        # add branch to stack
        stack.append(commit)

        while stack:
            # pop off last commit
            current_commit = stack.pop()
            # print(current_commit)
            # create commit node object
            c_object = CommitNode(current_commit)

            # get git object
            decompressed_data = os.popen("git cat-file -p " + current_commit).read()
            # get the strings
            strings = decompressed_data.split("\n")
            has_parents = False
            # find strings that start with parent and store them as parents in the commitnode object
            for string in strings:
                if string.startswith("parent"):
                    parent = string[7:]
                    # add parent to parent set
                    c_object.parents.add(parent)
                    stack.append(parent)
                    has_parents = True

            # if commit has no parents, it is a root commit
            if has_parents == False:
                root_commits.add(current_commit)

            if current_commit in graph:
                pass
            else:
                # store commit object in graph
                graph[current_commit] = c_object

    # populate DAG with children using parental relationships
    for commit, node in graph.items():
        # get "parent" commits
        parents = node.parents
        # for each parent commit, add current commit as child
        for p in parents:
            parentnode = graph[p]
            parentnode.children.add(commit)

    return graph, root_commits


"""
This function does a topological sort using breadth first search.
It then prints it in reverse so that the earliest commits are at the end of the list.
"""


def topo_sort():
    graph, roots = getGraph()
    result = []
    queue = deque()

    for root in roots:
        queue.append(root)

    while queue:
        # pop
        current = queue.popleft()
        # add to result
        result.append(current)
        # for each child
        for child in graph[current].children:
            # remove parent from child
            graph[child].parents.remove(current)
            # append child
            if len(graph[child].parents) == 0:
                queue.append(child)

    return result[::-1]


def topo_order_commits():
    graph, _ = getGraph()
    order = topo_sort()
    htb = map_hash_to_branch()
    empty_line = False

    for i in range(len(order) - 1):
        # get commit
        commit = order[i]
        # get node object of current node
        node = graph[commit]

        if empty_line == True:
            # sticky start
            print("=")
            for child in node.children:
                print(child, end="")
            print("")
            # if tip, print branch
            if commit in htb:
                print(commit, htb[commit])
            else:
                print(commit)
            empty_line = False
        # next commit is parent of current commit
        elif order[i + 1] in node.parents:
            # if tip, print branch
            if commit in htb:
                print(commit, htb[commit])
            else:
                print(commit)
        else:
            # if tip, print branch
            if commit in htb:
                print(commit, htb[commit])
            else:
                print(commit)
            # sticky end
            for parent in node.parents:
                print(parent + " ", end="")
            print("=")
            print("")
            empty_line = True

    commit = order[-1]
    if commit in htb:
        print(commit, htb[commit])
    else:
        print(commit)


if __name__ == "__main__":
    topo_order_commits()
