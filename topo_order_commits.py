#!/usr/bin/python3

import os, sys, zlib
from collections import deque


class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()


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


def getBranch():
    path = getPath() + "/.git/refs/heads"
    branches = dict()

    for root, dirs, files in os.walk(path):
        for f in files:
            branch = root + "/" + f
            head = branch[branch.rfind("heads/") + 6 :]
            commit = (open(branch).read()).strip()
            branches[head] = commit

    print(branches)
    return branches


# returns dictionary where branch name outputted when given commit hash
def map_hash_to_branch():
    branch = getBranch()
    hash_to_branch = dict()  # maps hash to branch name
    for b, commit in branch.items():
        hash_to_branch[commit] = b
    return hash_to_branch


def getGraph():
    # path
    path = getPath() + "/.git/objects"
    # branch
    branch = getBranch()

    # dictionary
    graph = dict()  # maps hash to commitnode object
    stack = []
    root_commits = set()

    # loops through all branches
    for b, commit in branch.items():
        # add branch to stack
        stack.append(commit)

        while stack:
            # pop off last commit
            current_commit = stack.pop()
            # create commit node object
            c_object = CommitNode(current_commit)

            # obtain parent
            decompressed_data = os.popen("git cat-file -p " + current_commit).read()
            # parents: add to set and stack
            strings = decompressed_data.split("\n")
            has_parents = False
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

    # populate DAG with children
    for commit, node in graph.items():
        # get "parent" commits
        parents = node.parents
        # for each parent commit, add current commit as child
        for p in parents:
            parentnode = graph[p]
            parentnode.children.add(commit)

    return graph, root_commits


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
            print("=", end="")
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

    if commit in htb:
        print(commit, htb[commit])
    else:
        print(commit)


if __name__ == "__main__":
    topo_order_commits()
