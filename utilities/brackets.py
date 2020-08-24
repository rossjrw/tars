import sys


def bracketify(string, bracket="()"):
    """Return a bool indicating that the string is missing an opening
    bracket"""
    opening = bracket[0]
    closing = bracket[1]
    depths = [0]
    for char in string:
        if char == opening:
            depths.append(depths[-1] + 1)
        elif char == closing:
            depths.append(depths[-1] - 1)
        else:
            depths.append(depths[-1])
    string = opening * -min(depths) + string
    string += closing * depths[-1]
    return string


if __name__ == '__main__':
    print(bracketify(sys.argv[1]))
